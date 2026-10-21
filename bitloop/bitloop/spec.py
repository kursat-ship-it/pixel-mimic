"""Spec (JSON) → normalised timeline. ONE clock: segments, music sections, transitions, captions and SFX are all
placed in BEATS (quarter notes) and converted to seconds through the tempo map (timing.TempoMap), so meter and
tempo changes / ritardandos stay in sync everywhere.

There is no fixed template: `segments` is a free list. Archetypes (archetypes.py) are optional starting points."""
import json, math, os, re
from . import transitions as TR
from .timing import tempo_map

ROLES = ["hook", "promise", "step", "build", "hold", "drop", "hit", "rehook", "number", "twist", "reveal", "payoff",
         "metaphor", "system", "contrast", "loop", "free"]
REHOOK_ROLES = {"rehook", "number", "twist", "reveal", "payoff", "drop", "hit", "contrast"}
PAYOFF_ROLES = {"reveal", "payoff", "metaphor"}
DEFAULT_ENERGY = {"hero": 1.0, "lattice": 2.0, "chain": 2.0, "streaks": 2.5, "pod": 2.0, "junction": 1.5,
                  "network": 2.5, "silhouette": 2.0, "object": 1.5, "image": 1.5, "void": .5,
                  "fractal_staff": 1.5, "koch": 2.0, "noise_scope": 2.0, "series_tree": 2.0, "shepard_stairs": 1.5,
                  "mandel_zoom": 3.0, "future_book": 1.5, "laplace_demon": 2.0, "dominoes": 2.0, "libet_clock": 1.5,
                  "future_tree": 2.5}
LEGIBLE_OBJECTS = {"jar", "can", "battery", "phone", "vinyl", "book"}
RISER_KINDS = {"noise", "shepard"}
SLOT = re.compile(r"\{\{[^}]+\}\}")
EVENT_SFX = {"punch": "thud", "flash": "flash", "pop": "pop", "shake": None, "pulse": None, "rehook": None, "twist": None,
             "reveal": "shimmer", "mark": None}


class SpecError(Exception):
    pass


def load(path):
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    spec["_dir"] = os.path.dirname(os.path.abspath(path))
    return normalise(spec)


# brand layer — constant for the channel; music/edit are designed per video
PRESETS = {
    "hayret": {"palette": "hayret", "music": {"logo": True}, "brand": {"handle": "@hayret.piksel", "auto": True},
               "fx": {"shimmer": .05}},
    "reference": {"palette": "violet-amber", "music": {"style": "reference", "logo": False}, "brand": {"handle": "", "auto": False},
                  "fx": {"shake": 0, "flash": 0, "shimmer": 0}},
}


# pacing — how hard the edit hits. "calm" (default since Oct 2026): narration-first, transitions every ~3–5 s,
# soft shake/flash, slower parallax. "punchy": the original 2-s cut, crash/whip-heavy feel (the first two reels).
PACING = {
    "calm": {"fx": {"shake": 1.0, "flash": .22}, "punch": .05, "flash_event": .35, "pulse": .12, "crash_beats": 2.0,
             "crash_zoom": 3.5, "morph_beats": 2.0, "layer_speed": .6, "transition_scale": 1.6,
             "static_max": 4.5, "avg_change": (1.0, 3.5), "seg_avg_min": 2.5, "fast_per_10s": 1.0,
             "cam": {"zoom_per_s": .35, "pan_per_s": 30.0, "rot_per_s": 6.0, "orbit": 4.0}},
    "punchy": {"fx": {"shake": 2.5, "flash": .55}, "punch": .12, "flash_event": .6, "pulse": .3, "crash_beats": 1.2,
               "crash_zoom": 7.0, "morph_beats": 1.5, "layer_speed": 1.0, "transition_scale": 1.0,
               "static_max": 3.0, "avg_change": (0.0, 2.5), "seg_avg_min": 0.0, "fast_per_10s": 99.0,
               "cam": None},
}
FAST_TRANSITIONS = {"crash", "whip", "spin", "glitch", "flash", "mosaic", "portal", "split"}
SCALE_TRANSITIONS = {"whip", "slide", "push", "mosaic", "glitch", "match", "flash", "spin", "tiles", "iris", "crt", "portal", "silhouette", "dissolve"}


def pace(s):
    p = s.get("pacing", "calm")
    base = PACING[p if isinstance(p, str) else p.get("preset", "calm")]
    return {**base, **({k: v for k, v in p.items() if k != "preset"} if isinstance(p, dict) else {})}


def _merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict):
            _merge(dst.setdefault(k, {}), v)
        else: dst.setdefault(k, v)


def auto_brand(s):
    """Diegetic tag placement when the spec placed none itself:
    1) legible label on the payoff object (reveal/payoff/metaphor segment; a billboard if that isn't an object),
    2) one subtle prop in an early middle segment chosen from its backdrop (ship in stars, neon on a skyline,
       terminal over a grid), 3) the eye mark as a constellation in every star field (layers.Stars)."""
    from .layers import DEFAULT_STACK
    b = s["brand"]
    if not b.get("auto") or not b.get("handle"): return
    segs = s.get("segments", [])
    if any(g.get("props") for g in segs) or any(g.get("params", {}).get("brand") not in (None, "", "auto", True)
                                                 for g in segs if g.get("scene") == "object"):
        return
    pay = [g for g in segs if g.get("role") in PAYOFF_ROLES] or [g for g in segs[::-1] if g.get("role") != "loop"][:1]
    if pay:
        g = pay[0]
        if g.get("scene") == "object": g.setdefault("params", {})["brand"] = b["handle"]
        else: g.setdefault("props", []).append({"kind": "billboard", "x": 0, "y": 105, "s": 1.0, "layer": "front", "par": 1.0, "_auto": True})
    for g in segs[1:]:
        if g.get("role") in PAYOFF_ROLES | {"hook", "loop"} or g.get("props"): continue
        back = (g.get("layers", {}).get("back") or DEFAULT_STACK.get(g.get("scene"), ([], []))[0])
        names = [n if isinstance(n, str) else n.get("kind") for n in back]
        pick = ({"kind": "ship", "x": 0, "y": -128, "s": .55, "layer": "back", "par": .35, "speed": 30, "span": 320} if "stars" in names else
                {"kind": "neon_sign", "x": 0, "y": -120, "s": .7, "layer": "back", "par": .35} if "skyline" in names else
                {"kind": "terminal", "x": 50, "y": -110, "s": .6, "layer": "back", "par": .35} if "grid" in names else None)
        if pick: pick["_auto"] = True; g["props"] = [pick]; break


def normalise(s):
    from . import music as M
    from .theory import register_series
    try: register_series((s.get("music") or {}).get("series_defs"))
    except Exception as e: s["_series_error"] = str(e)
    s.setdefault("version", 2)
    legacy = s["version"] < 2
    _merge(s, PRESETS[s.setdefault("preset", "hayret")])
    pc = s["_pace"] = pace(s)
    if s["preset"] != "reference": _merge(s, {"fx": pc["fx"]})
    s.setdefault("meta", {}); s["meta"].setdefault("lang", "tr")
    fmt = s.setdefault("format", {})
    fmt.setdefault("width", 1080); fmt.setdefault("height", 1920); fmt.setdefault("fps", 30); fmt.setdefault("grid", 6)
    s.setdefault("palette", "hayret")
    s.setdefault("loop", True); s.setdefault("loop_beats", 2.0)
    s.setdefault("crash_beats", pc["crash_beats"]); s.setdefault("morph_beats", pc["morph_beats"]); s.setdefault("dust", True)
    from . import narration as N
    nd = s.get("narration_defaults") or {}
    segs = s.setdefault("segments", [])
    for i, g in enumerate(segs):
        g.setdefault("id", f"S{i + 1}"); g.setdefault("role", "free"); g.setdefault("params", {})
        g.setdefault("camera", {}); g.setdefault("seed", 1000 + i * 17); g.setdefault("events", [])
        tr = TR.normalise(g.get("transition_in", "cut"), legacy)
        if tr["type"] == "crash": tr["beats"] = float(g["transition_in"].get("beats", s["crash_beats"])) if isinstance(g.get("transition_in"), dict) else s["crash_beats"]
        if tr["type"] == "dissolve" and g.get("transition_in") == "morph": tr["beats"] = s["morph_beats"]
        elif tr["type"] in SCALE_TRANSITIONS and not (isinstance(g.get("transition_in"), dict) and "beats" in g["transition_in"]):
            tr["beats"] = round(tr["beats"] * pc["transition_scale"] * 4) / 4
        g["_tr"] = tr; g["transition_in"] = tr["type"]
        if g.get("role") == "loop" and "energy" not in g and segs:
            g["energy"] = segs[0].get("energy", DEFAULT_ENERGY.get(segs[0].get("scene"), 1.0))
        g.setdefault("energy", DEFAULT_ENERGY.get(g.get("scene"), 1.5))
        g["captions"] = g.get("captions") or ([g["caption"]] if g.get("caption") else [])
        nar = g.get("narration") or []
        g["narration"] = [N.normalise_block(b, nd) for b in (nar if isinstance(nar, list) else [nar])]

    def seg_beats(meter_at):
        out, b = [], 0.0
        for g in segs:
            nb = float(g["beats"]) if "beats" in g else float(g.get("bars", 2)) * meter_at(b).bar_beats
            out.append(nb); b += nb
        return out
    nbs, total = M.resolve(s, seg_beats)
    s["total_beats"] = total
    tm = tempo_map(s)
    b0 = 0.0
    for g, nb in zip(segs, nbs):
        g["start_beat"], g["end_beat"] = b0, b0 + nb
        g["start_s"], g["end_s"] = tm.time(b0), tm.time(b0 + nb)
        b0 += nb
    s["duration_s"] = tm.time(total); s["beat_s"] = 60.0 / s["music"]["bpm"]
    lt = s.get("loop_transition", {"type": "dissolve", "beats": s["loop_beats"]})
    s["_loop_tr"] = {**TR.normalise(lt), "align": "end"}
    auto_brand(s)
    for g in segs:
        if g.get("scene") == "object" and g["params"].get("brand") in ("auto", True):
            g["params"]["brand"] = s["brand"]["handle"] if s["brand"].get("auto") else ""
    return s


def beat_time(s, b): return tempo_map(s).time(b)


def caption_items(s):
    """Captions in absolute seconds (+ the loop-return of the first caption)."""
    items = []; tm = tempo_map(s); T = s["duration_s"]
    for gi, g in enumerate(s["segments"]):
        for c in g["captions"]:
            a0, a1 = c.get("at", [1, 5.5])
            t0, t1 = tm.time(g["start_beat"] + a0), tm.time(g["start_beat"] + a1)
            it = {"text": c["text"], "hi": tuple(c.get("hi", ())), "t0": t0, "t1": min(t1, T), "seg": g["id"]}
            if gi == 0 and a0 <= 0 and s["loop"]:
                it["no_fade_in"] = True
                items.append({"text": c["text"], "hi": it["hi"], "t0": tm.time(s["total_beats"] - s["loop_beats"] * .5),
                              "t1": T + 1, "no_fade_out": True, "seg": "loop"})
            items.append(it)
    return items


# ------------------------------------------------------------------ the one event timeline
def _scene_sfx(g, spec):
    from .scenes import SCENES
    class P:
        def ramp(self, n, t):
            import numpy as np; return np.zeros(3, np.float32)
    if "{{" in json.dumps(g["params"], ensure_ascii=False) or g.get("scene") not in SCENES: return []
    try: sc = SCENES[g["scene"]]({**g["params"]}, g["seed"], P(), spec.get("_dir", ".")).bind(g, spec)
    except Exception: return []
    dur = g["end_beat"] - g["start_beat"]
    return [(g["start_beat"] + (b if b >= 0 else dur + b), k) for b, k in sc.sfx(dur)]


def timeline_events(spec):
    """[(beat, sfx_kind, label)] — drives SFX (music.py), shake/flash (render.py) and the retention map."""
    ev = []
    segs = spec["segments"]
    for i, g in enumerate(segs):
        for b, k in _scene_sfx(g, spec): ev.append((b, k, f"{g['id']}:scene"))
        tr = g["_tr"]
        if i and tr["type"] != "cut" and tr.get("sfx"): ev.append((g["start_beat"], tr["sfx"], f"{g['id']}:trans:{tr['type']}"))
        for c in g["captions"]:
            a0 = c.get("at", [1, 5])[0]
            if not (i == 0 and a0 <= 0): ev.append((g["start_beat"] + a0, "tick", f"{g['id']}:caption"))
        for e in g["events"]:
            k = e.get("sfx", EVENT_SFX.get(e.get("kind"), None))
            if k: ev.append((g["start_beat"] + float(e.get("at", 0)), k, f"{g['id']}:event:{e.get('kind')}"))
        for p in g.get("props", []):
            if p.get("kind") == "stamp": ev.append((g["start_beat"] + float(p.get("at", 1.0)), "thud", f"{g['id']}:stamp"))
    for sec in spec["_sections"]:
        if sec["drop"] and not any(k in ("hit", "boom", "drop") and abs(b - sec["b0"]) < .15 for b, k, _ in ev):
            ev.append((sec["b0"], "hit", f"{sec['name']}:drop"))
        if sec["riser"] and sec.get("riser_kind", "noise") == "noise": ev.append((sec["b1"], "riser", f"{sec['name']}:riser"))
    if any(g.get("narration") for g in segs):
        from .narration import blocks
        for B in blocks(spec):
            for b, k in B["blips"]: ev.append((b, k, f"{B['sid']}:narration"))
    if spec.get("loop") and spec["_loop_tr"].get("sfx") and spec["_loop_tr"]["type"] not in ("cut", "dissolve"):
        ev.append((spec["total_beats"], spec["_loop_tr"]["sfx"], "loop:trans"))
    return sorted(ev, key=lambda e: e[0])


def visual_hits(spec):
    """Seconds of shake+flash (hits/drops) and of punch-ins, from the same timeline."""
    tm = tempo_map(spec); hits, punches, flashes = [], [], []
    pc = spec.get("_pace") or pace(spec)
    for b, k, lab in timeline_events(spec):
        if k in ("hit", "boom", "drop"): hits.append(tm.time(b))
    for g in spec["segments"]:
        for e in g["events"]:
            t = tm.time(g["start_beat"] + float(e.get("at", 0)))
            if e.get("kind") == "shake": hits.append(t)
            if e.get("kind") == "punch": punches.append((t, float(e.get("amount", pc["punch"]))))
            if e.get("kind") in ("flash", "pulse"): flashes.append((t, float(e.get("amount", pc["flash_event"] if e["kind"] == "flash" else pc["pulse"]))))
    return sorted(set(hits)), punches, flashes


def brand_placements(s):
    out = []
    for g in s["segments"]:
        if g.get("scene") == "object" and g["params"].get("brand"):
            out.append((g["id"], g["start_beat"] + float(g["params"].get("brand_at", 1.0)), "label:" + g["params"].get("kind", "bulb"),
                        g["params"].get("kind", "bulb") in LEGIBLE_OBJECTS or "{{" in str(g["params"].get("kind", ""))))
        from .scenes import SCENES
        cls = SCENES.get(g.get("scene"))
        if cls is not None and hasattr(cls, "brand_tags"):      # scenes that paint the handle themselves (chalk_unify)
            for at, kind, leg in cls.brand_tags(g.get("params") or {}):
                out.append((g["id"], g["start_beat"] + float(at), kind, bool(leg)))
        for p in g.get("props", []):
            k = p["kind"]; sc = float(p.get("s", 1.0))
            leg = p.get("legible", k == "billboard" or (k in ("neon_sign", "chalkboard", "stamp") and sc >= .9) or (k == "plate" and sc >= 1.3))
            out.append((g["id"], g["start_beat"] + float(p.get("from", 0)), k, bool(leg)))
    return out


# ------------------------------------------------------------------ validation + retention map
def _cap_kind(t):
    t = t.replace("*", "")
    return "question" if "?" in t else "number" if re.search(r"\d", t) else "claim" if "!" in t else "text"


def retention(s):
    """-> dict with ordered rows [(t, beat, lane, text)] + metrics used by validate()."""
    tm = tempo_map(s); T = s["duration_s"]; segs = s["segments"]
    rows, changes, rehooks = [], [0.0], []
    caps = caption_items(s)
    for i, g in enumerate(segs):
        tr = g["_tr"]
        lane = "HOOK" if i == 0 else ("CUT" if tr["type"] == "cut" else "TRANS")
        lab = f"{g['id']} {g['role']:<8} {g['scene']}" + ("" if i == 0 else f"  ← {tr['type']}" + (f" ({tr['beats']:g}b)" if tr["beats"] else ""))
        rows.append((g["start_s"], g["start_beat"], lane, lab)); changes.append(g["start_s"])
        if i and tr["type"] != "cut":
            w0, w1 = TR.window(tr, g["start_beat"]); changes += [tm.time(w0), tm.time(w1)]
        if g["role"] in REHOOK_ROLES or g.get("rehook"):
            rehooks.append((g["start_s"], g["role"]))
        c = g["camera"]; z = c.get("zoom", [1, 1]); pan = c.get("pan", [[0, 0], [0, 0]])
        big = max(z) / max(min(z), 1e-3) >= 1.3 or math.hypot(pan[1][0] - pan[0][0], pan[1][1] - pan[0][1]) >= 25 or abs(c.get("rot", [0, 0])[1] - c.get("rot", [0, 0])[0]) >= 8
        if big:
            mid = (g["start_s"] + g["end_s"]) / 2; changes += [mid]
            if g["end_s"] - g["start_s"] > 4: changes += [g["start_s"] + (g["end_s"] - g["start_s"]) * q for q in (.25, .75)]
        for e in g["events"]:
            t = tm.time(g["start_beat"] + float(e.get("at", 0))); changes.append(t)
            rows.append((t, g["start_beat"] + float(e.get("at", 0)), "EVENT", f"{e.get('kind')}" + (f" · {e['label']}" if e.get("label") else "")))
            if e.get("kind") in ("rehook", "twist", "reveal"): rehooks.append((t, e["kind"]))
        for p in g.get("props", []):
            if float(p.get("from", 0)) > 0: changes.append(tm.time(g["start_beat"] + float(p["from"])))
        for b, k in _scene_sfx(g, s): changes.append(tm.time(b))
    for c in caps:
        if c["seg"] == "loop": continue
        k = _cap_kind(c["text"]); short = c["text"].replace("\n", " / ")
        rows.append((c["t0"], tm.beat(c["t0"]), "TEXT", f"“{short}”" + ("" if k == "text" else f"  [{k}]")))
        changes += [c["t0"], c["t1"]]
        if k != "text": rehooks.append((c["t0"], k))
    from .narration import blocks as _nblocks
    text_ch = []
    nar = _nblocks(s) if any(g.get("narration") for g in segs) else []
    for B in nar:
        txt = re.sub(r"[*_]", "", B["b"]["text"]).replace("\n", " "); k = _cap_kind(txt)
        short = txt if len(txt) <= 44 else txt[:42] + "…"
        rows.append((B["t0"], B["t"]["start"], "TEXT", f"“{short}” ({B['b']['reveal']}, {B.get('placed', B['b']['place'])})" + ("" if k == "text" else f"  [{k}]")))
        text_ch += [B["t0"], B["t1"]]
        # a revealing block is a visual change: one per second of reveal (+ its completion)
        n = max(1, int(B["t_full"] - B["t0"]))
        text_ch += [B["t0"] + (B["t_full"] - B["t0"]) * q / n for q in range(1, n + 1)]
        if k != "text": rehooks.append((B["t0"], k))
    for sec in s["_sections"]:
        tag = []
        if sec["drop"]: tag.append("DROP")
        if sec["riser"]: tag.append("riser→" if sec.get("riser_kind", "noise") == "noise" else f"{sec['riser_kind']} riser→")
        if sec["stop"]: tag.append(f"stop {sec['stop']:g}b")
        bpm = f"{sec['bpm']:g}" + (f"→{sec['bpm_to']:g}" if sec["bpm_to"] != sec["bpm"] else "")
        rows.append((tm.time(sec["b0"]), sec["b0"], "MUSIC", f"{sec['name']}: e{sec['energy']:g} {sec['meter']} {bpm} BPM {sec['key']} {sec['scale']} {' '.join(tag)}"))
        if sec["drop"]: rehooks.append((tm.time(sec["b0"]), "drop")); changes.append(tm.time(sec["b0"]))
    from .music import logo_targets
    for lb in logo_targets(s): rows.append((tm.time(min(lb, s["total_beats"])), lb, "LOGO", "sonic logo (long note)"))
    for sid, b, kind, leg in brand_placements(s):
        rows.append((tm.time(b), b, "TAG", f"@ {kind} {'LEGIBLE' if leg else 'subtle'} ({sid})"))
    if s.get("loop"): rows.append((T, s["total_beats"], "LOOP", f"seam ← {s['_loop_tr']['type']} → frame 0"))
    rows.sort(key=lambda r: (r[0], r[2]))
    scene_changes = sorted(set(round(c, 3) for c in changes + [T] if 0 <= c <= T))
    changes = sorted(set(round(c, 3) for c in changes + text_ch + [T] if 0 <= c <= T))
    gaps = [(b - a, a) for a, b in zip(changes, changes[1:])]
    holds = []
    for sec in s["_sections"]:
        if sec["stop"]: holds.append((tm.time(sec["b1"] - sec["stop"]), tm.time(sec["b1"])))
    rh = sorted(set(round(t, 2) for t, _ in rehooks))
    rgaps = [b - a for a, b in zip([0.0] + rh, rh + [T])]
    return {"rows": rows, "changes": changes, "gaps": gaps, "rehooks": rh, "rehook_gaps": rgaps, "holds": holds, "captions": caps,
            "narration": nar, "scene_changes": scene_changes}


def lane_strip(s, R, res=.5):
    T = s["duration_s"]; n = int(math.ceil(T / res)); lane = ["·"] * n
    pri = {"·": 0, "\"": 1, "|": 2, "!": 3, "▲": 4, "♪": 5, "@": 6, "↻": 7}
    def put(t, ch):
        i = min(n - 1, max(0, int(t / res)))
        if pri[ch] > pri[lane[i]]: lane[i] = ch
    for t, b, ln, txt in R["rows"]:
        ch = {"TEXT": "\"", "CUT": "|", "TRANS": "|", "HOOK": "!", "LOGO": "♪", "LOOP": "↻"}.get(ln)
        if ln == "TAG" and "LEGIBLE" in txt: ch = "@"
        if ln == "MUSIC" and "DROP" in txt: ch = "▲"
        if ln == "TEXT" and "[" in txt: ch = "!"
        if ch: put(t, ch)
    for t in R["rehooks"]: put(t, "!")
    ruler = "".join(f"{int(k * res):<10d}" if k % 10 == 0 else "" for k in range(0, n, 10))
    return ruler[:n + 4], "".join(lane)


def retention_map(s):
    R = retention(s); out = []
    secs = s["_sections"]
    meters = "→".join(dict.fromkeys(x["meter"] for x in secs)); bpms = "→".join(dict.fromkeys(f"{x['bpm']:g}" for x in secs))
    out.append(f"RETENTION MAP · {s['duration_s']:.1f} s · {meters} · {bpms} BPM · {len(s['segments'])} segments")
    r1, r2 = lane_strip(s, R)
    out += ["  s  " + r1, "     " + r2, "     legend: ! hook/re-hook  | cut/transition  \" caption  ▲ drop  ♪ sonic logo  @ legible tag  ↻ loop"]
    out.append(f"  {'t(s)':>6} {'beat':>6}  {'lane':<6} event")
    for t, b, ln, txt in R["rows"]: out.append(f"  {t:6.2f} {b:6.2f}  {ln:<6} {txt}")
    g = max(R["gaps"]) if R["gaps"] else (0, 0)
    out.append(f"  visual change every {s['duration_s'] / max(1, len(R['changes']) - 1):.2f} s on average · longest static {g[0]:.2f} s at {g[1]:.2f} s"
               f" · longest re-hook gap {max(R['rehook_gaps'][:-1] or [0]):.1f} s · {len(R['rehooks'])} hooks/re-hooks")
    return "\n".join(out), R


def validate(s, strict=False):
    """-> (errors, warnings): brand + quality + retention rules (no fixed template)."""
    from .scenes import SCENES
    from .captions import coverage, upper
    from .layers import DEFAULT_STACK
    E, W = [], []
    raw = json.dumps({k: v for k, v in s.items() if not k.startswith("_")}, ensure_ascii=False)
    if SLOT.search(raw): E.append("unfilled template slots: " + ", ".join(sorted(set(SLOT.findall(raw)))[:12]))
    segs = s.get("segments") or []
    if not segs: E.append("no segments"); return E, W
    from . import narration as N
    tm = tempo_map(s); T = s["duration_s"]; handle = s["brand"].get("handle", "")
    rd = {**N.READ, **(s.get("readability") or {})}; pc = s.get("_pace") or pace(s)
    for g in segs:
        sid = g["id"]
        if g.get("scene") not in SCENES: E.append(f"{sid}: unknown scene '{g.get('scene')}' ({', '.join(SCENES)})")
        if g["role"] not in ROLES: W.append(f"{sid}: role '{g['role']}' is not a known role ({', '.join(ROLES)})")
        if g["end_beat"] - g["start_beat"] <= 0: E.append(f"{sid}: duration must be > 0")
        if abs(g["start_beat"] * 2 - round(g["start_beat"] * 2)) > 1e-6: W.append(f"{sid}: starts off the beat grid (beat {g['start_beat']:.3f}; cut on ½-beats)")
        _validate_vision(s, g, sid, E)
        lay = g.get("layers") or {}
        db, df = DEFAULT_STACK.get(g.get("scene"), ([], []))
        nl = len(lay.get("back", db)) + len(lay.get("front", df))
        nl += int(getattr(SCENES.get(g.get("scene")), "own_layers", 0))   # depth layers a scene draws itself (haze, stars, ridges)
        if nl < 3: E.append(f"{sid}: only {nl} moving layers (brand rule ≥ 3)")
        for c in g["captions"]:
            t = c.get("text", "")
            if handle and (handle.lower() in t.lower() or "hayret.piksel" in t.lower()):
                E.append(f"{sid}: the channel handle may not appear in captions (diegetic tag only)")
            lines = [l for l in re.split(r"\n|\s/\s", upper(t.replace("*", ""), s["meta"]["lang"])) if l.strip()]
            if len(lines) > 3: E.append(f"{sid}: caption has {len(lines)} lines (max 3 — use a narration block for sentences)")
            for l in lines:
                if "{{" in l or "}}" in l: continue
                d = cap_dot(l, s["format"]["width"])
                if d < N.MIN_DOT: E.append(f"{sid}: caption line '{l}' would render at {d} px/dot (< legible minimum {N.MIN_DOT}) — use narration")
            miss = [] if "{{" in t else coverage(t, s["meta"]["lang"])
            if miss: E.append(f"{sid}: font lacks glyphs {miss}")
            a0, a1 = c.get("at", [1, 5.5])
            if a1 > g["end_beat"] - g["start_beat"] + 1e-6: W.append(f"{sid}: caption ends after the segment")
            need = rd["base"] + rd["per_word"] * N.word_count(t.replace("/", " "))
            have = tm.time(g["start_beat"] + a1) - tm.time(g["start_beat"] + a0) - .2
            if "{{" not in t and have < need - 1e-6 and not (g is segs[0] and a0 <= 0 and s["loop"]):
                W.append(f"{sid}: caption '{t[:24].replace(chr(10), ' / ')}' readable {have:.1f} s < {need:.1f} s needed ({N.word_count(t)} words)")
        for k in ("image",):
            pth = g["params"].get(k)
            if pth and "{{" not in pth and not os.path.exists(pth if os.path.isabs(pth) else os.path.join(s.get("_dir", "."), pth)):
                E.append(f"{sid}: {k} file not found: {pth}")
        sh = g["params"].get("shape") or g["params"].get("inner")
        if isinstance(sh, str) and sh.lower().endswith((".png", ".jpg")) and not os.path.isabs(sh) and not os.path.exists(os.path.join(s.get("_dir", "."), sh)):
            E.append(f"{sid}: mask file not found: {sh}")
    m = s["music"]
    if m["source"] == "file":
        f = m.get("file")
        if not f or not os.path.exists(f if os.path.isabs(f) else os.path.join(s.get("_dir", "."), f)): E.append(f"music file not found: {f}")
    from .theory import SERIES
    if s.get("_series_error"): E.append(f"music.series_defs: {s['_series_error']}")
    for name, d in (m.get("series_defs") or {}).items():
        vals = d if isinstance(d, list) else (d or {}).get("values")
        if not vals or not all(isinstance(x, int) for x in vals): E.append(f"series_defs {name}: values must be a non-empty list of ints")
        if name in ("norgard",): E.append(f"series_defs {name}: name clashes with a built-in series")
    for name, v in (m.get("voices") or {}).items():
        if not v or not v.get("series"): continue
        ss = v["series"] if isinstance(v["series"], dict) else {"name": v["series"]}
        if ss.get("name", "norgard") not in SERIES: E.append(f"voice {name}: unknown series '{ss.get('name')}' ({', '.join(SERIES)})")
        r = float(ss.get("rate", v.get("rate", 4))) / float(ss.get("div", 1) or 1)
        if not 0 < r <= 8: E.append(f"voice {name}: series rate {r:g} notes/beat out of range (0, 8]")
        if ss.get("phase", "global") not in ("global", "section"): E.append(f"voice {name}: series phase must be global|section")
        if not isinstance(ss.get("lookahead", 0), int) or not 0 <= ss.get("lookahead", 0) <= 64: E.append(f"voice {name}: series lookahead must be an int 0..64")
    from .music import ARP as _ARP, BASS as _BASS
    _known = {"arp": set(_ARP) | {"oompah", "groups", "random"}, "bass": set(_BASS) | {"sustain", "groups", "waltz"}}
    for vn, v in list((m.get("voices") or {}).items()) + [(f"{r.get('name')}.{k}", vv) for r in (m.get("sections") or [])
                                                          if isinstance(r.get("voices"), dict) for k, vv in r["voices"].items() if isinstance(vv, dict)]:
        if not isinstance(v, dict) or v.get("series") or not isinstance(v.get("pattern"), str): continue
        role = v.get("role", vn if vn in _known else None)
        if role in _known and v["pattern"] not in _known[role]:
            W.append(f"voice {vn}: unknown {role} pattern '{v['pattern']}' (silently plays the default; {', '.join(sorted(_known[role]))})")
    for r in m.get("sections") or []:
        if r.get("riser_kind", "noise") not in RISER_KINDS: E.append(f"section {r.get('name')}: unknown riser_kind '{r.get('riser_kind')}' ({', '.join(sorted(RISER_KINDS))})")
        if r.get("riser_kind") and not r.get("riser"): W.append(f"section {r.get('name')}: riser_kind set but riser is false")
    for sec in s["_sections"]:
        if not 60 <= sec["bpm"] <= 180 or not 60 <= sec["bpm_to"] <= 180: W.append(f"section {sec['name']}: tempo outside 60–180 BPM")
        if sec["stop"] and tm.time(sec["b1"]) - tm.time(sec["b1"] - sec["stop"]) > 1.5: W.append(f"section {sec['name']}: held breath > 1.5 s")
    # duration / text
    if not 15 <= T <= 90: E.append(f"duration {T:.1f} s outside 15–90 s")
    elif not 20 <= T <= 45: W.append(f"duration {T:.1f} s outside the 20–45 s sweet spot")
    _validate_narration(s, E, W, N, rd, handle)
    _validate_motion(s, W, pc)
    # brand
    bp = brand_placements(s)
    if handle and not any(leg for *_, leg in bp): E.append("the tag never appears legibly (needs ≥ 1 legible placement: object label / billboard / big neon)")
    if len(bp) > 3: W.append(f"{len(bp)} tag placements (brand rule: ≤ 3 — 1 legible + 1–2 subtle)")
    if any(tm.time(b) < 2.0 for _, b, _, _ in bp): W.append("tag visible in the first 2 s (no logo intro — hook first)")
    # retention
    R = retention(s); caps = [c for c in R["captions"] if c["seg"] != "loop"]
    nar = R["narration"]
    starts = [c["t0"] for c in caps] + [B["t0"] + (tm.time(B["t"]["start"] + B["t"]["lead"]) - B["t0"]) for B in nar]
    first = min(starts, default=None)
    if first is None or first > 2.0: E.append("no hook caption in the first 2 s")
    elif first > 1.5: W.append(f"hook caption at {first:.2f} s (aim 0–1.5 s)")
    hook_nar = [B for B in nar if B["t0"] <= 1.5 and "{{" not in B["b"]["text"]]
    if hook_nar and not caps and min(B["t_full"] for B in hook_nar) > 3.0:
        W.append(f"hook narration fully revealed only at {min(B['t_full'] for B in hook_nar):.1f} s (keep the hook ≤ ~3 s: shorter text or a faster rate)")
    if segs[0]["scene"] == "void": W.append("hook scene is 'void' (frame 1 needs motion + a subject)")
    early = [c for c in caps if c["t0"] <= 3.0 and _cap_kind(c["text"]) != "text"] + \
            [B for B in nar if B["t0"] <= 3.0 and _cap_kind(B["b"]["text"]) != "text"]
    if not early: W.append("no curiosity gap / bold claim in the first 3 s (question, number or '!')")
    holds = R["holds"]
    for d, a in R["gaps"]:
        if d > pc["static_max"] and not any(h0 - .05 <= a and a + d <= h1 + .05 for h0, h1 in holds):
            W.append(f"static stretch {d:.1f} s at {a:.1f}–{a + d:.1f} s (add a cut/transition/event or reveal text; max {pc['static_max']:g} s)")
    avg = T / max(1, len(R["changes"]) - 1); lo, hi = pc["avg_change"]
    if avg > hi: W.append(f"visual change every {avg:.1f} s on average (aim {max(lo, 1.5) if lo else 1.5:g}–{hi:g} s)")
    elif T / max(1, len(R["scene_changes"]) - 1) < lo: avg = T / max(1, len(R["scene_changes"]) - 1); W.append(f"visual change every {avg:.1f} s on average — too busy for calm pacing (aim {lo:g}–{hi:g} s)")
    if R["rehook_gaps"] and max(R["rehook_gaps"][:-1] or [0]) > 8.0:
        W.append(f"re-hook gap {max(R['rehook_gaps'][:-1]):.1f} s (aim every 5–8 s: new question / number / reveal / drop)")
    tw = [g for g in segs if g["role"] == "twist"] + [g for g in segs for e in g["events"] if e.get("kind") == "twist"]
    if not any(.3 <= g["start_s"] / T <= .8 for g in tw): W.append("no mid-video twist (role or event 'twist' at 30–80 %)")
    pay = [g for g in segs if g["role"] in PAYOFF_ROLES]
    if not any(g["start_s"] / T >= .45 for g in pay): W.append("no payoff in the second half (role reveal/payoff/metaphor)")
    en = [(x["b0"], x["energy"]) for x in s["_sections"]]; half = s["total_beats"] / 2
    en2 = [(x["b0"], x["b1"], x["energy"]) for x in s["_sections"]]
    if en2 and max((e for b0, b1, e in en2 if b1 > half), default=0) < max((e for b0, b1, e in en2 if b0 < half), default=0):
        W.append("energy peaks in the first half (escalate stakes toward the payoff)")
    types = [g["transition_in"] for g in segs[1:]]
    if len(types) >= 5 and len(set(types)) < 3: W.append("fewer than 3 transition types (pattern breaks keep attention)")
    for a, b, c in zip(types, types[1:], types[2:]):
        if a == b == c and a != "cut": W.append(f"three '{a}' transitions in a row"); break
    if not s.get("loop"): W.append("loop=false (seamless rewatch loop recommended)")
    meta = s["meta"]
    if meta.get("title") and len(meta["title"]) > 70: W.append("title > 70 chars")
    if meta.get("hashtags") is not None and not 3 <= len(meta["hashtags"]) <= 6: W.append("use 3–6 hashtags")
    return E, W


def _validate_vision(s, g, sid, E):
    """segment.vision / segment.palette / params.peek|collapse modes must resolve (vision.resolve)."""
    from . import vision as V
    from .palette import Palette
    names = [g.get("vision")] + [(g.get("params") or {}).get(k, {}).get(f) for k, f in (("peek", "mode"), ("collapse", "from"))
                                 if isinstance((g.get("params") or {}).get(k), dict)]
    for n in names:
        if n is None: continue
        try: V.resolve(s, n)
        except Exception as e: E.append(f"{sid}: {e}")
    if g.get("palette") is not None:
        try: Palette(g["palette"])
        except Exception as e: E.append(f"{sid}: bad palette ({e})")


def cap_dot(line, W=1080):
    """px per dot a legacy caption line renders at (captions auto-shrink from 12)."""
    from .pixfont import line_bitmap
    m, _ = line_bitmap([(line, False)]); dot = max(1, round(W * 12 / 1080))
    while m.shape[1] * dot + 48 > int(W * .93) and dot > 1: dot -= 1
    return dot


def _validate_narration(s, E, W, N, rd, handle):
    segs = s["segments"]
    if not any(g.get("narration") for g in segs): return
    for B in N.blocks(s):
        b, sid, k = B["b"], B["sid"], B["i"] + 1; t = b["text"]; tag = f"{sid}: narration {k}"
        if "{{" in t: continue
        if b["place"] not in N.PLACES: E.append(f"{tag}: unknown place '{b['place']}' ({', '.join(N.PLACES)})")
        if b["reveal"] not in N.REVEALS: E.append(f"{tag}: unknown reveal '{b['reveal']}' ({', '.join(N.REVEALS)})")
        if b["exit"] not in N.EXITS: E.append(f"{tag}: unknown exit '{b['exit']}' ({', '.join(N.EXITS)})")
        if isinstance(b["rate"], str) and b["rate"] != "auto" and b["rate"] not in N.RATES: E.append(f"{tag}: unknown rate '{b['rate']}'")
        if handle and (handle.lower() in t.lower() or "hayret.piksel" in t.lower()):
            E.append(f"{tag}: the channel handle may not appear in narration (diegetic tag only)")
        miss = N.missing(t, b.get("case"))
        if miss: E.append(f"{tag}: font lacks glyphs {miss}")
        if b["place"] != "world" and B["dot"] < N.MIN_DOT:
            E.append(f"{tag}: {B['dot']} px/dot is below the legible minimum {N.MIN_DOT}")
        size = b["size"] if isinstance(b["size"], str) else ("body" if B["dot"] < 9 else "head" if B["dot"] < 12 else "title")
        mx = N.MAX_LINES.get(size, 5)
        if len(B["lines"]) > mx: W.append(f"{tag}: {len(B['lines'])} lines (max {mx} at size '{size}'; split it into two blocks)")
        p = B["t"]; have = B["t_exit"] - B["t_full"]
        if have < p["read_s"] - 1e-6:
            W.append(f"{tag}: on screen {max(have, 0):.1f} s after full reveal < {p['read_s']:.1f} s reading time ({p['words']} words) — "
                     f"lengthen 'until'/the segment, use a faster rate or shorten the text")
        if b["reveal"] in ("type", "word", "line") and p["rate"]:
            q = min(p["rate"], 1.0)
            if abs((p["start"] / q) - round(p["start"] / q)) > 1e-6:
                W.append(f"{tag}: starts off the {q:g}-beat grid (beat {p['start']:g}) — reveal won't sit on the music")
        g = segs[B["seg"]]
        if p["end"] > g["end_beat"] + 1e-6 and b.get("until") not in ("auto", None): W.append(f"{tag}: runs past its segment")
    try:
        from .render import Film
        f = Film(s)
        for m in f.narr.report: W.append(m)
        for B in f.narr.blocks:
            if B["b"]["place"] == "world" and not B.get("_loop"):
                d = f.narr.world_screen_dot(B)
                if d < N.MIN_DOT - 1e-6: W.append(f"{B['sid']}: in-world narration {B['i'] + 1} shrinks to {d:.1f} px/dot on screen (< {N.MIN_DOT}; raise surface.dot or zoom in)")
    except Exception as e:                       # layout check is best effort (e.g. unfilled template slots)
        if not SLOT.search(json.dumps([g.get("params") for g in segs], ensure_ascii=False)): W.append(f"narration layout check skipped: {e}")


def _validate_motion(s, W, pc):
    """Calm-pacing rules: cut rhythm, fast-transition budget, camera speed, fx intensity."""
    segs = s["segments"]; T = s["duration_s"]; cam = pc.get("cam")
    real = [g for g in segs if g["role"] != "loop"]
    if pc["seg_avg_min"] and len(real) > 1:
        avg = sum(g["end_s"] - g["start_s"] for g in real) / len(real)
        if avg < pc["seg_avg_min"]: W.append(f"segments average {avg:.1f} s (calm pacing: a new shot every ~3–5 s)")
    fast = [g["transition_in"] for g in segs[1:] if g["transition_in"] in FAST_TRANSITIONS]
    if len(fast) > max(1, round(pc["fast_per_10s"] * T / 10)):
        W.append(f"{len(fast)} fast transitions ({', '.join(fast)}) — calm pacing allows ~{pc['fast_per_10s']:g} per 10 s; prefer dissolve/match/slide/iris")
    if cam:
        for g in segs:
            c = g["camera"]; d = max(g["end_s"] - g["start_s"], 1e-3)
            z = c.get("zoom", [1, 1]); pan = c.get("pan", [[0, 0], [0, 0]]); rot = c.get("rot", [0, 0])
            zr = abs(math.log(max(z[1], 1e-3) / max(z[0], 1e-3))) / d
            pr = math.hypot(pan[1][0] - pan[0][0], pan[1][1] - pan[0][1]) / d; rr = abs(rot[1] - rot[0]) / d
            why = [f"zoom {zr:.2f}/s > {cam['zoom_per_s']:g}" for _ in [0] if zr > cam["zoom_per_s"]] + \
                  [f"pan {pr:.0f} px/s > {cam['pan_per_s']:g}" for _ in [0] if pr > cam["pan_per_s"]] + \
                  [f"rot {rr:.1f}°/s > {cam['rot_per_s']:g}" for _ in [0] if rr > cam["rot_per_s"]] + \
                  [f"orbit {abs(c.get('orbit', 0)):g}° > {cam['orbit']:g}" for _ in [0] if abs(c.get("orbit", 0)) > cam["orbit"]]
            if why and g["role"] != "hook": W.append(f"{g['id']}: fast camera ({'; '.join(why)}) — calm pacing")
    fx = s.get("fx", {})
    if pc["fx"]["shake"] < 2 and fx.get("shake", 0) > 2: W.append(f"fx.shake {fx['shake']:g} is punchy (calm ≤ 2)")
    if pc["fx"]["flash"] < .4 and fx.get("flash", 0) > .4: W.append(f"fx.flash {fx['flash']:g} is punchy (calm ≤ .4)")


def table(s):
    rows = [f"{'id':4} {'role':9} {'scene':10} {'beats':>5} {'start':>6} {'end':>6}  {'in':8} caption"]
    for g in s["segments"]:
        cap = " | ".join([c["text"].replace("\n", " / ") for c in g["captions"]] + [f"[{b['place']}] " + b["text"].replace("\n", " ")[:40] for b in g.get("narration") or []])
        rows.append(f"{g['id']:4} {g['role']:9} {g['scene']:10} {g['end_beat'] - g['start_beat']:5.1f} {g['start_s']:6.2f} {g['end_s']:6.2f}  {g['transition_in']:8} {cap}")
    rows.append(f"total {s['total_beats']:.1f} beats = {s['duration_s']:.2f} s")
    return "\n".join(rows)
