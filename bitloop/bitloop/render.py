"""Frame renderer + exporter. Frame(t) is a pure function of the spec, so frames render in parallel workers."""
import json, math, os, subprocess, sys, tempfile, time
import numpy as np
from .palette import Palette, BAYER4
from .raster import Canvas, Camera
from .scenes import SCENES, ease
from .captions import CaptionStyle, CaptionTrack
from .layers import LAYERS, DEFAULT_STACK, scanline_shimmer, with_par
from .props import PROPS
from . import spec as specmod
from . import transitions as TR
from .timing import tempo_map
from .shapes import load_mask
from . import vision as V


def lerp(a, b, k): return a + (b - a) * k


class Film:
    def __init__(self, spec):
        self.s = spec
        f = spec["format"]; self.W, self.H, self.fps, self.g = f["width"], f["height"], f["fps"], f["grid"]
        self.aw, self.ah = self.W // self.g, self.H // self.g
        self.pal = Palette(spec["palette"])          # brand palette: captions + narration colours (never changes)
        self.cv = Canvas(self.aw, self.ah, self.pal)
        self.cv2 = Canvas(self.aw, self.ah, self.pal)
        # per-segment vision mode + output palette; vision segments draw their world (scene, back layers, back/mid
        # props) as ALBEDO in the world palette, then the mode maps the G-buffer and quantises to its own palette
        self.world_pal = Palette(spec.get("world_palette") or spec["palette"])
        self.seg_vis = [V.resolve(spec, g.get("vision")) for g in spec["segments"]]
        self.seg_pal = [Palette(g["palette"]) if g.get("palette") else (v.pal if v else self.pal)
                        for g, v in zip(spec["segments"], self.seg_vis)]
        self._union = {}; self._hits = {}
        self.scenes = [SCENES[g["scene"]](g["params"], g["seed"], self.world_pal if v else p, spec.get("_dir", ".")).bind(g, spec)
                       for g, v, p in zip(spec["segments"], self.seg_vis, self.seg_pal)]
        for sc in self.scenes:
            if hasattr(sc, "attach"): sc.attach(self)
        self.beat = spec["beat_s"]; self.T = spec["duration_s"]; self.tm = tempo_map(spec)
        st = CaptionStyle(self.W, self.H, self.pal, lang=spec["meta"]["lang"], grid=self.g)
        self.caps = CaptionTrack(specmod.caption_items(spec), st)
        self._abs_t = None
        self.stacks = []
        for i, g in enumerate(spec["segments"]):
            back, front = g.get("layers", {}).get("back"), g.get("layers", {}).get("front")
            db, df = DEFAULT_STACK.get(g["scene"], (["nebula", "stars"], ["bokeh", "dust"]))
            mk = lambda names, off, pal: [LAYERS[n if isinstance(n, str) else n["kind"]](g["seed"] + off + k * 31, pal,
                                     **({} if isinstance(n, str) else {kk: vv for kk, vv in n.items() if kk != "kind"}))
                                     for k, n in enumerate(names)]
            if g.get("layer_sync") in ("first", "loop") and i > 0 and spec.get("loop"):
                self.stacks.append(self.stacks[0]); continue       # loop segment re-uses frame 0's layer objects
            bp = self.world_pal if self.seg_vis[i] else self.seg_pal[i]
            self.stacks.append((mk(back if back is not None else db, 5, bp), mk(front if front is not None else df, 900, self.seg_pal[i])))
        # one timeline → hits (shake + colour flash), punch-ins, extra flashes
        self.hits, self.punches, self.flashes = specmod.visual_hits(spec)
        pc = spec.get("_pace") or specmod.pace(spec); self.pace = pc
        fx = spec.get("fx", {}); self.shake_amp = fx.get("shake", pc["fx"]["shake"]); self.flash_k = fx.get("flash", pc["fx"]["flash"])
        self.layer_speed = float(fx.get("layer_speed", pc["layer_speed"]))
        self.shimmer = fx.get("shimmer", .05)
        self.shim_p = self.T / max(1, round(self.T / 3.0))     # integer cycles per film → loop-safe
        # transition windows (seconds) per boundary i (between i-1 and i); the loop seam is boundary len(segs)
        segs = spec["segments"]; self.windows = []
        for i in range(1, len(segs)):
            tr = segs[i]["_tr"]
            if tr["type"] in ("cut", "crash", "match") or tr["beats"] <= 0: continue
            w0, w1 = TR.window(tr, segs[i]["start_beat"])
            self.windows.append((self.tm.time(w0), self.tm.time(w1), i - 1, i, tr))
        if spec["loop"]:
            tr = spec["_loop_tr"]; w0, _ = TR.window({**tr, "align": "end"}, spec["total_beats"])
            self.windows.append((self.tm.time(w0), self.T, len(segs) - 1, 0, tr))
        self._masks = {}
        from .narration import NarrationTrack
        crect = [(it["t0"], it["t1"], (it["x"], it["y"], it["x"] + it["arr"].shape[1], it["y"] + it["arr"].shape[0])) for it in self.caps.items]
        self.narr = NarrationTrack(self, crect)

    def _mask(self, name, size):
        key = (name, size)
        if key not in self._masks:
            m = load_mask(name, self.s.get("_dir", ".")); S = m.shape[0]; side = int(self.aw * size)
            yy, xx = np.mgrid[0:self.ah, 0:self.aw]
            u = ((xx - self.aw / 2) / side + .5) * S; v = ((yy - self.ah / 2) / side + .5) * S
            ok = (u >= 0) & (u < S) & (v >= 0) & (v < S); out = np.zeros((self.ah, self.aw), bool)
            out[ok] = m[v[ok].astype(int), u[ok].astype(int)] > 0
            self._masks[key] = out
        return self._masks[key]

    def _lb(self, i, t):
        """local beat of segment i at absolute time t (via the tempo map; negative before its start)."""
        return float(self.tm.beat(t)) - self.s["segments"][i]["start_beat"]

    # ----- camera for segment i at local beat lb
    def camera(self, i, lb):
        g = self.s["segments"][i]; c = g["camera"]; dur = g["end_beat"] - g["start_beat"]
        k = ease(lb / dur, c.get("ease", "inOutSine"))
        z = c.get("zoom", [1, 1]); pan = c.get("pan", [[0, 0], [0, 0]]); rot = c.get("rot", [0, 0])
        zoom = math.exp(lerp(math.log(z[0]), math.log(z[1]), k))           # log-space zoom = constant-feel speed
        cx, cy = lerp(pan[0][0], pan[1][0], k), lerp(pan[0][1], pan[1][1], k)
        r = math.radians(lerp(rot[0], rot[1], k) + c.get("orbit", 0) * math.sin(lb * math.pi / max(dur, 1)))
        if c.get("follow"):
            fx, fy = self.scenes[i].focus(lb, dur); w = c.get("follow", 1.0) if isinstance(c.get("follow"), (int, float)) else 1.0
            cx, cy = lerp(cx, fx, w), lerp(cy, fy, w)
        # crash-zoom: if the NEXT segment enters with 'crash', dive into this scene's focus at the end
        segs = self.s["segments"]
        if i + 1 < len(segs) and segs[i + 1]["transition_in"] == "crash":
            cb = segs[i + 1]["_tr"]["beats"]; kk = (lb - (dur - cb)) / cb
            if kk > 0:
                kk = ease(kk, "inExpo"); fx, fy = self.scenes[i].focus(lb, dur)
                zoom *= math.exp(math.log(c.get("crash_zoom", self.pace["crash_zoom"])) * kk); cx, cy = lerp(cx, fx, kk), lerp(cy, fy, kk)
        # portal: the OUTGOING scene dives into its focus with a live (redrawn) camera over the whole portal window,
        # instead of a nearest-neighbour bitmap blow-up of the finished frame (which produced fat, uneven pixels)
        if i + 1 < len(segs) and segs[i + 1]["_tr"]["type"] == "portal":
            ptr = segs[i + 1]["_tr"]; w0, w1 = TR.window(ptr, dur); pw = max(w1 - w0, 1e-6)
            kk = (lb - w0) / pw
            if kk > 0:
                kk = min(kk, 1.0) ** 2; fx, fy = self.scenes[i].focus(lb, dur)
                zoom *= math.exp(math.log(ptr.get("dive", 6.0)) * kk); cx, cy = lerp(cx, fx, kk), lerp(cy, fy, kk)
        tr = g["_tr"]
        if i > 0 and tr["type"] == "match" and 0 <= lb < tr["beats"] and not getattr(self, "_in_match", False):
            self._in_match = True
            try:
                p = segs[i - 1]; pd = p["end_beat"] - p["start_beat"]
                pc = self.camera(i - 1, pd); pf = self.scenes[i - 1].focus(pd, pd); nf = self.scenes[i].focus(lb, dur)
                sx, sy = (pf[0] - pc.cx) * pc.zoom / zoom, (pf[1] - pc.cy) * pc.zoom / zoom   # old focus' screen offset
                kk = 1 - ease(lb / tr["beats"], "outCubic")
                cx, cy = lerp(cx, nf[0] - sx, kk), lerp(cy, nf[1] - sy, kk)
            finally:
                self._in_match = False
        if self._abs_t is not None:
            for tp, amt in self.punches:
                dt = self._abs_t - tp
                if 0 <= dt < .5: zoom *= 1 + amt * math.exp(-dt * 9)
        if self.shake_amp and self._abs_t is not None:
            for h in self.hits:
                dt = self._abs_t - h
                if 0 <= dt < .7:
                    a = self.shake_amp * math.exp(-dt * 7) / zoom
                    cx += a * math.sin(dt * 91 + h); cy += a * math.cos(dt * 77 + 2 * h)
        return Camera(cx, cy, zoom, r)

    def _flash(self, t):
        k = 0.0
        for h in self.hits:
            dt = t - h
            if 0 <= dt < .35: k = max(k, math.exp(-dt * 13))
        k *= self.flash_k
        for tf, amt in self.flashes:
            dt = t - tf
            if 0 <= dt < .3: k = max(k, amt * math.exp(-dt * 14))
        return k

    def drum_hits(self, inst):
        """Beats of every audible hit of drum `inst` (music.drum_hits) — picture sync (sonar rings on 'B')."""
        if inst not in self._hits:
            from .music import drum_hits
            try: self._hits[inst] = drum_hits(self.s, inst)
            except Exception: self._hits[inst] = []
        return self._hits[inst]

    def _clock(self, g, i, lt, lb, t_abs):
        dur = g["end_beat"] - g["start_beat"]; llt, llb = lt, lb
        if g.get("layer_sync") in ("first", "loop") and i > 0 and self.s.get("loop"):
            # layers run on the film-loop clock (t − T): at the seam they are exactly frame 0's layers
            llt = (t_abs - self.T) if t_abs is not None else lt - (g["end_s"] - g["start_s"]); llb = lb - dur
        ls = self.layer_speed
        return llt * ls, llb * ls      # calm pacing: slower parallax/particles (seam-safe: 0 ↦ 0)

    def _post(self, cv, t_abs):
        cv.vignette()
        if t_abs is not None:
            k = self._flash(t_abs)
            if k > 0:
                cv.rgb += np.asarray(cv.pal.ramp("energy", 1.0)) * k; cv.rgb *= 1 + .3 * k
            if self.shimmer: scanline_shimmer(cv.rgb, (t_abs % self.shim_p) / self.shim_p, self.shimmer)

    def _draw_scene(self, cv, i, lt, lb, t_abs=None):
        g = self.s["segments"][i]; dur = g["end_beat"] - g["start_beat"]
        self._abs_t = t_abs
        if self.seg_vis[i] is not None and not getattr(self.scenes[i], "final", False):
            return self._draw_vision(cv, i, lt, lb, t_abs)
        cv.pal = self.seg_pal[i]
        cv.set_cam(self.camera(i, lb)); cv.clear()
        back, front = self.stacks[i]
        llt, llb = self._clock(g, i, lt, lb, t_abs)
        if getattr(self.scenes[i], "final", False):          # scene composes its own final, quantised image
            return self.scenes[i].final_image(cv, lt, lb, dur, t_abs)
        for L in back: L.render(cv, llt, llb)
        self._props(cv, i, lt, lb, "back")
        self.scenes[i].draw(cv, lt, lb, dur)
        self._props(cv, i, lt, lb, "mid")
        if t_abs is not None and self.narr.blocks: self.narr.draw_world(cv, i, t_abs)
        for L in front: L.render(cv, llt, llb)
        self._props(cv, i, lt, lb, "front")
        self._post(cv, t_abs)
        return cv.composite()

    # ----- vision segments: world → G-buffer → mode map(s) → front stage → mode palette
    def _aux_stage(self, cv, fn, depth, oid, lum_ids=False):
        """Run a draw stage; pixels it changed get default aux (uv .3·lum, temp .2, depth, oid). lum_ids: oid + 4
        luminance steps so painted letters on a prop become sonar edges."""
        before = cv.rgb.copy(); fn()
        ch = np.abs(cv.rgb - before).max(-1) > 2e-3
        if not ch.any(): return
        lum = np.clip(cv.rgb @ np.array([.3, .59, .11], np.float32), 0, 1)
        o = oid + (np.round(lum * 4).astype(np.int32) if lum_ids else 0)
        cv.put_aux(ch, uv=.3 * lum, temp=.2, depth=depth, oid=o)

    def vision_ctx(self, i, cv, lb):
        """Map context: sonar origin (screen px) + live rings from the segment's `sonar` params."""
        g = self.s["segments"][i]; sp = g["params"].get("sonar")
        if not sp: return {}
        sc = self.scenes[i]; dur = g["end_beat"] - g["start_beat"]
        ox, oy = sc.anchor(sp.get("origin", "focus"), lb) if hasattr(sc, "anchor") else sc.focus(lb, dur)
        X, Y = cv.to_screen(ox, oy)
        return {"origin": (float(X), float(Y)), "rings": self.sonar_rings(sp, g["start_beat"] + lb), "base": float(sp.get("base", 0.0))}

    def sonar_rings(self, sp, B):
        src = str(sp.get("rings_on", "drum:B")); speed = float(sp.get("speed", 300.0)); per = float(sp.get("persistence_beats", 1.5))
        if src.startswith("drum:"): hits = self.drum_hits(src[5:])
        else: hits = [float(x) for x in sp.get("hits", [])]
        live = [h for h in hits if 0 <= B - h < per][-int(sp.get("max_rings", 3)):]
        return [((B - h) * speed, 1 - (B - h) / per) for h in live]

    def vision_mix(self, i, lb):
        """[(Vision, share)] extra modes dithered over the main one: params.peek (blink) / params.collapse."""
        p = self.s["segments"][i]["params"]; out = []
        pk = p.get("peek")
        if pk:
            u = (lb - float(pk.get("at", 0))) / max(float(pk.get("beats", .75)), 1e-6)
            if 0 < u < 1: out.append((V.resolve(self.s, pk["mode"]), min(1.0, 1.6 * math.sin(math.pi * u))))
        cl = p.get("collapse")
        if cl:
            u = lb / max(float(cl.get("beats", 1.0)), 1e-6)
            if u < 1: out.append((V.resolve(self.s, cl["from"]), 1 - ease(max(u, 0.0), "inOutSine")))
        return out

    def _draw_vision(self, cv, i, lt, lb, t_abs):
        g = self.s["segments"][i]; dur = g["end_beat"] - g["start_beat"]; sc = self.scenes[i]
        cv.enable_aux(); cv.pal = self.world_pal
        cv.set_cam(self.camera(i, lb)); cv.clear()
        back, front = self.stacks[i]
        llt, llb = self._clock(g, i, lt, lb, t_abs)
        self._aux_stage(cv, lambda: [L.render(cv, llt, llb) for L in back], 1.0, 0)
        self._props(cv, i, lt, lb, "back", aux=.9)
        if getattr(sc, "writes_aux", False): sc.draw(cv, lt, lb, dur)
        else: self._aux_stage(cv, lambda: sc.draw(cv, lt, lb, dur), .5, 50)
        self._props(cv, i, lt, lb, "mid", aux=.5)
        G = {"rgb": np.clip(cv.rgb + cv.glowbuf, 0, 1), **{k: v.copy() for k, v in cv.aux.items()}}
        ctx = self.vision_ctx(i, cv, lb)
        modes = [(self.seg_vis[i], 1.0, self.seg_pal[i])] + [(m, sh, m.pal) for m, sh in self.vision_mix(i, lb)]
        out = None
        for m, share, pal in modes:
            cv.rgb[:] = V.apply(m, G, ctx); cv.glowbuf[:] = 0; cv.pal = pal
            if t_abs is not None and self.narr.blocks: self.narr.draw_world(cv, i, t_abs)
            for L in front: L.render(cv, llt, llb)
            self._props(cv, i, lt, lb, "front")
            self._post(cv, t_abs)
            img = V.quantize(cv.rgb + cv.glowbuf, pal, m.pixel, m.spread)
            out = img if out is None else V.dither_mix(out, img, share)
        cv.pal = self.seg_pal[i]
        return out

    def _props(self, cv, i, lt, lb, layer, aux=None):
        for k, pr in enumerate(self.s["segments"][i].get("props", [])):
            if pr.get("layer", "mid") != layer: continue
            if not (pr.get("from", -1e9) <= lb <= pr.get("to", 1e9)): continue
            fn = PROPS[pr["kind"]]
            opt = {kk: v for kk, v in pr.items() if kk not in ("kind", "x", "y", "s", "layer", "par", "from", "to", "handle", "depth")}
            handle = pr.get("handle", self.s["brand"]["handle"])
            draw = lambda: fn(cv, cv.pal, lt, lb, pr.get("x", 0), pr.get("y", 0), pr.get("s", 1.0), handle, **opt)
            par = pr.get("par", .3 if layer == "back" else (1.3 if layer == "front" else 1.0))
            run = draw if par == 1.0 else (lambda: with_par(cv, par, draw))
            if pr.get("legible"): run = self._matte_glow(cv, run)
            if aux is None: run()
            else: self._aux_stage(cv, run, float(pr.get("depth", aux)), 200 + 8 * k, lum_ids=True)

    @staticmethod
    def _matte_glow(cv, run):
        """Legible tags sit ON TOP of scene light: clear the additive glow under the pixels the prop drew, so lamp /
        sun glows can't dither cream lettering into a pale checker (QC canli-gozu S9 hive label); the same pixels skip
        the vignette (a label near the frame edge was shaded to a cream/mist checker)."""
        def go():
            before = cv.rgb.copy(); run()
            ch = np.abs(cv.rgb - before).max(-1) > 2e-3
            if ch.any():
                cv.glowbuf[ch] = 0
                cv.keep = ch if getattr(cv, "keep", None) is None else (cv.keep | ch)
        return go

    def seg_index(self, t):
        for i, g in enumerate(self.s["segments"]):
            if t < g["end_s"]: return i
        return len(self.s["segments"]) - 1

    def _scene_img(self, cv, i, t):
        g = self.s["segments"][i]; lt = t - g["start_s"]
        return self._draw_scene(cv, i, lt, self._lb(i, t), t)

    def _focus_px(self, i, t):
        g = self.s["segments"][i]; lb = self._lb(i, t); dur = g["end_beat"] - g["start_beat"]
        self.cv2.set_cam(self.camera(i, lb)); fx, fy = self.scenes[i].focus(lb, dur)
        X, Y = self.cv2.to_screen(fx, fy)
        return float(np.clip(X, 0, self.aw - 1)), float(np.clip(Y, 0, self.ah - 1))

    def art_frame(self, t):
        i = self.seg_index(t)
        for w0, w1, ia, ib, tr in self.windows:
            if w0 <= t < w1 or (ib == 0 and w0 <= t <= w1):
                k = (float(self.tm.beat(t)) - float(self.tm.beat(w0))) / max(float(self.tm.beat(w1)) - float(self.tm.beat(w0)), 1e-6)
                tb = t - self.T if ib == 0 else t                    # loop seam: incoming = the film's frame 0 timeline
                a = self._scene_img(self.cv, ia, t)
                b = self._scene_img(self.cv2, ib, tb)
                ctx = {"focus_a": self._focus_px(ia, t), "focus_b": self._focus_px(ib, tb), "seed": ib * 7919,
                       "mask": self._mask}
                return TR.apply(tr, a, b, k, self._tr_pal(ia, ib), ctx)
        return self._scene_img(self.cv, i, t)

    def _tr_pal(self, ia, ib):
        pa, pb = self.seg_pal[ia], self.seg_pal[ib]
        if pa is pb or (pa.colors.shape == pb.colors.shape and np.allclose(pa.colors, pb.colors)): return pb
        if (ia, ib) not in self._union: self._union[(ia, ib)] = V.union_palette([pa, pb], pb)
        return self._union[(ia, ib)]

    def _dissolve(self, a, b, k):
        """Radial-from-centre ordered dither dissolve (no flat 'screen-door' veil)."""
        h, w = a.shape[:2]
        by = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]
        yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot((xx - w / 2) / w, (yy - h / 2) / h) / .72
        thr = np.clip(k * 1.6 - r * .6, 0, 1)
        m = by < thr
        out = a.copy(); out[m] = b[m]; return out

    def frame(self, t):
        a = self.art_frame(t)
        big = np.repeat(np.repeat(a, self.g, 0), self.g, 1)
        out = self.caps.composite(np.ascontiguousarray(big), t)
        return self.narr.composite(out, t) if self.narr.blocks else out


# ---------------- multiprocessing
_F = None


def _init(spec_json):
    global _F
    _F = Film(json.loads(spec_json))


def _work(t):
    return _F.frame(t).tobytes()


def render(spec, out, fps=None, t0=0.0, t1=None, workers=None, crf=18, preset="medium", audio=True, log=print):
    from multiprocessing import get_context
    from .music import build_audio
    if fps: spec["format"]["fps"] = fps
    fps = spec["format"]["fps"]; W, H = spec["format"]["width"], spec["format"]["height"]
    T = spec["duration_s"]; t1 = T if t1 is None else min(t1, T)
    n = int(round((t1 - t0) * fps)); times = [t0 + k / fps for k in range(n)]
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="bitloop_")
    wav = None
    if audio:
        log("audio: synthesising / mastering…")
        wav = build_audio(spec, os.path.join(tmp, "audio.wav"))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-"]
    if wav:
        cmd += ["-ss", f"{t0:.4f}", "-t", f"{t1 - t0:.4f}", "-i", wav]
    cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-tune", "animation", "-pix_fmt", "yuv420p",
            "-profile:v", "high", "-level", "4.2", "-g", str(fps * 2), "-r", str(fps), "-color_primaries", "bt709",
            "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
            "-bsf:v", "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0"]
    if wav: cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-af", "apad", "-shortest"]   # pad: never drop the last video frame
    cmd += ["-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    workers = workers or max(1, (os.cpu_count() or 2) - 1)
    clean = {k: v for k, v in spec.items()}
    st = time.time()
    with get_context("fork").Pool(workers, _init, (json.dumps(clean, ensure_ascii=False),)) as pool:
        for k, buf in enumerate(pool.imap(_work, times, chunksize=4)):
            p.stdin.write(buf)
            if k % (fps * 2) == 0:
                log(f"  frame {k}/{n}  {k / max(time.time() - st, 1e-3):.1f} fps")
    p.stdin.close(); rc = p.wait()
    import shutil; shutil.rmtree(tmp, ignore_errors=True)            # temp audio
    if rc: raise RuntimeError("ffmpeg failed")
    log(f"wrote {out}  ({n} frames, {time.time() - st:.1f}s)")
    return out


def still(spec, t, path=None, scale=1.0):
    from PIL import Image
    f = Film(spec); im = Image.fromarray(f.frame(t))
    if scale != 1: im = im.resize((int(im.width * scale), int(im.height * scale)), Image.NEAREST)
    if path: im.save(path)
    return im


def sheet(spec, times, path, cols=6, w=270, label=True):
    from PIL import Image, ImageDraw
    f = Film(spec); h = int(w * f.H / f.W)
    rows = (len(times) + cols - 1) // cols
    out = Image.new("RGB", (cols * w, rows * (h + 18)), (12, 8, 16)); d = ImageDraw.Draw(out)
    for k, t in enumerate(times):
        im = Image.fromarray(f.frame(t)).resize((w, h), Image.BILINEAR)
        x, y = (k % cols) * w, (k // cols) * (h + 18)
        out.paste(im, (x, y + 18))
        if label:
            seg = f.s["segments"][f.seg_index(t)]["id"]
            d.text((x + 4, y + 3), f"{t:.2f}s {seg}", fill=(255, 220, 120))
    out.save(path, quality=90); return path
