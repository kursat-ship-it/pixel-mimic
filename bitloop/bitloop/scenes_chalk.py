"""chalk_unify: ONE classroom chalkboard that persists across consecutive segments (S2→S3→S4 of evren-anlamak).

The scene finds its run (consecutive segments using chalk_unify) in bind() and plays every segment's writing on the
run's global-beat timeline, so whatever was written stays on the board (chalk dust and handwriting continue across
the cuts/transitions; a later segment only adds). The slate is drawn by the scene in the palette's `board` ramp
(fallback: bg) inside a wooden frame, with a chalk tray, smudges of erased writing and drifting dust.

segment params
  (default mode)  left, right      two formulas hand-written in chalk (pixfont incl. Greek), left then right
                  merge_at         beat: they slide together, puff, and fuse into one line `merged` ("? = ?")
                  labels           [left label, right label] in yellow micro-chalk (default GÖRELİLİK / KUANTUM)
                  corner_note      small coral note (decor; give a callout the readable version), note_xy
                  formula_dot      world units per formula dot (1 = classic; 2 = phone-legible: both formulas centred,
                                   stacked, subscripts 12 output px per dot); label_font / note_font "mini" | "font"
                                   (font = the 5×7 pixfont with real Turkish glyphs instead of the 3×5 micro-chalk)
  mode calendar   year             tear-off calendar pinned to the board (swings in), `odds` written as "SON: <odds>"
                  year_from/to     pages flutter year_from → year_to over flip_beats (several flips)
                  odds_crossout_at beat: chalk strike through the odds; godel_note written in yellow below
  tag             "subtle" | "legible" | None: the channel handle in chalk at the board's lower right
                  (subtle = half-erased and small; legible = fresh chalk, pixel-snapped ≥ 6 output px per dot, and
                  exempt from glow + vignette). Registered for the brand validator via brand_tags()."""
import math
import numpy as np
from .scenes import Scene, SCENES, ease
from .bitmap import Bitmap, text_bitmap, draw_text, formula_bitmap
from .minifont import mini_bitmap
from .scenes_vision import vnoise, _h

TAU = math.pi * 2
BOARD = (-80.0, -100.0, 80.0, 34.0)          # inner slate x0, y0, x1, y1 (world units)
WOOD = ("#3A2414", "#5A3A22", "#8A5A32")


def _hex(h):
    h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def smooth(x, a, b):
    t = min(max((x - a) / (b - a), 0.0), 1.0); return t * t * (3 - 2 * t)


def chalk_blit(cv, arr, x, y, dot, color, alpha=1.0, reveal=1.0, seed=0.0, slant=.1, wobble=.45, grain=.22):
    """Hand-written chalk: bitmap `arr` centred at world (x, y), `dot` world units per dot, revealed left→right
    (`reveal` 0..1 of the columns), sheared + wobbling baseline, grainy (world-anchored dropout).
    → world position of the chalk tip (x, y) while writing, else None."""
    h, w = arr.shape
    if reveal <= 0: return None
    X, Y = cv.to_screen(x, y); R = cv.sl(max(w, h) * dot) * .75 + 3
    b = cv._box(float(X), float(Y), R)
    if b is None: return None
    wx, wy = cv.world_grid(); wx, wy = wx[b], wy[b]
    v = (wy - y) / dot + h / 2
    u = (wx - x) / dot + w / 2 + (v - h / 2) * slant
    v = v + wobble * np.sin(u * .23 + seed * 3.1)
    ok = (u >= 0) & (u < w * min(reveal, 1.0)) & (v >= 0) & (v < h)
    ink = ok & arr[np.clip(v.astype(int), 0, h - 1), np.clip(u.astype(int), 0, w - 1)]
    gr = _h(np.floor(wx * 1.7), np.floor(wy * 1.7), seed + .37)
    m = ink.astype(np.float32) * np.where(gr < grain, .25, np.where(gr < grain * 2, .7, 1.0)) * alpha
    cv._blend(b, m, cv._col(color))
    if reveal < 1:
        cu = w * reveal; cvv = h * .55
        return (x + (cu - w / 2 - (cvv - h / 2) * slant) * dot, y + (cvv - h / 2) * dot)
    return None


def _strip(a):
    rows = np.nonzero(a.any(1))[0]; return a[rows.min():rows.max() + 1] if len(rows) else a


def _font(text):
    return _strip(text_bitmap(text))


def _formula(text):
    return formula_bitmap(text, scale=1)


def _mini(text):
    return mini_bitmap(text)


class ChalkUnify(Scene):
    own_layers = 3                  # drifting chalk dust, board smudges/ghost writing (parallax-free) and the slate light
    defaults = {"left": "Gμν = 8πG Tμν", "right": "iħ ∂ψ/∂t = Ĥψ", "merge_at": 6.0, "merged": "? = ?",
                "labels": ["GÖRELİLİK", "KUANTUM"], "corner_note": "", "note_xy": [28.0, 26.0],
                "mode": None, "year": 1980, "odds": "%50", "year_from": None, "year_to": None, "flip_beats": 1.5,
                "odds_crossout_at": None, "godel_note": "", "tag": None, "tag_xy": [6.0, 15.0], "write_rate": 9.0,
                "formula_dot": 1.0, "label_font": "mini", "note_font": "mini"}

    @staticmethod
    def brand_tags(params):
        t = params.get("tag")
        return [(0.0, "chalk_tag", t == "legible")] if t else []

    # ---------------------------------------------------------------- run timeline
    def on_bind(self):
        self.run = [(self.b0, self.p)]; self._run_bound = False

    def bind(self, seg, spec):
        super().bind(seg, spec)
        segs = spec.get("segments", []); i = next((k for k, g in enumerate(segs) if g is seg or g.get("id") == seg.get("id")), None)
        if i is None: return self
        j = i
        while j > 0 and segs[j - 1].get("scene") == seg.get("scene"): j -= 1
        self.run = []
        for g in segs[j:i + 1]:
            raw = dict(g.get("params") or {})
            if raw.get("mode") == "calendar":            # a calendar segment adds to the board; it never rewrites formulas
                raw.setdefault("left", None); raw.setdefault("right", None)
            self.run.append((float(g.get("start_beat", 0.0)), {**self.defaults, **raw}))
        self.handle = (spec.get("brand") or {}).get("handle", "@hayret.piksel")
        self.run_b0 = self.run[0][0]
        return self

    handle = "@hayret.piksel"

    def _events(self, B):
        """→ dict of everything on the board at global beat B (merged over the run's segments so far)."""
        st = {"left": None, "right": None, "merge": None, "note": None, "cal": None, "odds": None, "cross": None,
              "godel": None, "tag": None}
        for b0, p in self.run:
            if B < b0 - 1e-9: break
            if p.get("left"): st["left"] = (b0 + .5, p["left"], p["labels"])
            if p.get("right"): st["right"] = (b0 + 2.6, p["right"])
            if p.get("left") and p.get("right") and p.get("merge_at") is not None: st["merge"] = (b0 + float(p["merge_at"]), p["merged"])
            if p.get("corner_note"): st["note"] = (b0 + 4.8, p["corner_note"], p["note_xy"], None)
            elif st["note"] and st["note"][3] is None: st["note"] = st["note"][:3] + (b0,)
            if p.get("mode") == "calendar":
                if p.get("year_from") is not None:
                    st["cal"] = ("flip", b0, int(p["year_from"]), int(p["year_to"]), float(p["flip_beats"]))
                else:
                    st["cal"] = ("pin", b0, int(p["year"]), None, 0.0)
                    if p.get("odds"): st["odds"] = (b0 + .5, "SON: " + str(p["odds"]))
                if p.get("odds_crossout_at") is not None: st["cross"] = b0 + float(p["odds_crossout_at"])
                if p.get("godel_note"): st["godel"] = (b0 + float(p.get("odds_crossout_at") or 2) + .3, p["godel_note"])
            st["tag"] = (b0, p.get("tag"))
        return st

    def focus(self, lb, dur_b):
        return (0.0, -30.0)

    # ---------------------------------------------------------------- draw
    def draw(self, cv, lt, lb, dur_b):
        B = self.gbeat(lb); st = self._events(B); pal = cv.pal
        self._room(cv, B)
        chalk = pal.ramp("pale", 1.0); yel = pal.ramp("energy", .72); cor = pal.ramp("accent", .62)
        tips = []
        p0 = self.run[0][1] if self.run else self.p          # board style comes from the run's first segment
        fd = float(p0.get("formula_dot", 1.0))
        lab = _font if p0.get("label_font") == "font" else _mini
        loff = (lambda a, l: 11.0) if fd == 1 else (lambda a, l: a.shape[0] * fd / 2 + l.shape[0] / 2 + 1.5)
        # --- the two formulas, then the merge
        mrg = st["merge"]; mk = 0.0 if mrg is None else smooth(B, mrg[0], mrg[0] + .6)
        gone = 0.0 if mrg is None else smooth(B, mrg[0] + .55, mrg[0] + .9)
        if st["left"]:
            t0, text, labels = st["left"]
            arr = _formula(text); n = arr.shape[1]
            rv = (B - t0) * self.p["write_rate"] * 6 / n
            lx, ly = (-8 + 8 * mk, -70 + 15 * mk) if fd == 1 else (0.0, -70 + 19 * mk)
            if gone < 1:
                tips.append(self._chalk_d(cv, gone, lambda: chalk_blit(cv, arr, lx, ly, fd, chalk, .97, rv, seed=1.0, wobble=.35, grain=.1)))
                if labels and rv > 1.1:
                    la = lab(labels[0]); rl = (B - t0 - n / (6 * self.p["write_rate"])) * 2.2
                    self._chalk_d(cv, gone, lambda: chalk_blit(cv, la, lx, ly + loff(arr, la), 1.0, yel, .9, rl, seed=4.0, slant=0, wobble=.15, grain=.06))
        if st["right"]:
            t0, text = st["right"]
            arr = _formula(text); n = arr.shape[1]
            rv = (B - t0) * self.p["write_rate"] * 6 / n
            rx, ry = (8 - 8 * mk, -40 - 15 * mk) if fd == 1 else (0.0, -32 - 19 * mk)
            if gone < 1:
                tips.append(self._chalk_d(cv, gone, lambda: chalk_blit(cv, arr, rx, ry, fd, chalk, .97, rv, seed=2.0, wobble=.35, grain=.1)))
                labs = st["left"][2] if st["left"] else None
                if labs and len(labs) > 1 and rv > 1.1:
                    la = lab(labs[1]); rl = (B - t0 - n / (6 * self.p["write_rate"])) * 2.2
                    self._chalk_d(cv, gone, lambda: chalk_blit(cv, la, rx, ry + loff(arr, la), 1.0, yel, .9, rl, seed=5.0, slant=0, wobble=.15, grain=.06))
        if mrg is not None and B >= mrg[0] + .5:
            self._puff(cv, B - (mrg[0] + .55))
            arr = _font(mrg[1]); rv = (B - mrg[0] - .85) * 2.0
            tips.append(chalk_blit(cv, np.kron(arr, np.ones((2, 2), bool)), 0, -55, 1.0, chalk, .97, rv, seed=3.0, slant=.06))
            if st["left"] and st["left"][2]:
                la = lab(" + ".join(st["left"][2])); rl = (B - mrg[0] - 1.6) * 1.6
                chalk_blit(cv, la, 0, -38, 1.0, yel, .9, rl, seed=6.0, slant=0, wobble=.15, grain=.06)
        if st["note"]:
            t0, text, (nx, ny), wipe = st["note"]
            g = 0.0 if wipe is None else smooth(B, wipe, wipe + .6)
            if g < 1:
                tips.append(self._chalk_d(cv, g, lambda: chalk_blit(cv, (_font if p0.get("note_font") == "font" else _mini)(text), nx, ny, 1.0, cor, .95, (B - t0) * 2.0, seed=7.0, slant=0, wobble=.15, grain=.06)))
        # --- calendar + odds + crossout + Gödel
        if st["cal"]: self._calendar(cv, B, st["cal"])
        if st["odds"]:
            t0, text = st["odds"]; arr = _font(text)
            tips.append(chalk_blit(cv, arr, 22, -12, 1.0, chalk, .95, (B - t0) * 1.3, seed=8.0, wobble=.3, grain=.12))
            if st["cross"] is not None and B >= st["cross"]:
                k = smooth(B, st["cross"], st["cross"] + .3)
                w = arr.shape[1]; x1 = 22 + w / 2 + 1; x0 = x1 - 20
                cv.line(x0, -9.5, x0 + (x1 - x0) * k, -15.5, 1.3, cor, .95)
                if B > st["cross"] + .3:
                    k2 = smooth(B, st["cross"] + .3, st["cross"] + .5)
                    cv.line(x0 + 1, -15, x0 + 1 + (x1 - x0 - 2) * k2, -10, 1.1, cor, .9)
                tips.append((x0 + (x1 - x0) * k, -12) if k < 1 else None)
        if st["godel"]:
            t0, text = st["godel"]
            tips.append(chalk_blit(cv, _font(text), 22, 0, 1.0, yel, .97, (B - t0) * 1.1, seed=9.0, wobble=.3, grain=.12))
        # --- the handle
        tb, kind = st["tag"]
        if kind: self._tag(cv, kind)
        for tip in tips:
            if tip: self._chalk_tip(cv, B, tip)
        self._dust(cv, B)

    @staticmethod
    def _chalk_d(cv, gone, fn):
        """draw `fn` and dither it away by `gone` (0 = all there, 1 = erased)"""
        if gone <= 0: return fn()
        before = cv.rgb.copy(); r = fn()
        from .palette import BAYER4
        by = np.tile(BAYER4, (cv.H // 4 + 1, cv.W // 4 + 1))[:cv.H, :cv.W]
        m = by < gone; cv.rgb[m] = before[m]
        return r

    def _room(self, cv, B):
        pal = cv.pal; x0, y0, x1, y1 = BOARD
        wall = pal.ramp("bg", .35)
        wx, wy = cv.world_grid()
        n = vnoise(wx / 9.0, wy / 23.0, 1.7)
        cv.rgb[:] = wall * (.85 + .3 * n[..., None])
        cv.rect(0, y1 + 70, 400, 60, pal.ramp("bg", .15), 1.0)                        # wainscot
        for k in range(-5, 6): cv.line(k * 34.0, y1 + 42, k * 34.0, y1 + 100, .6, pal.ramp("bg", .05), .8)
        cv.line(-200, y1 + 41, 200, y1 + 41, 1.0, _hex(WOOD[1]), 1.0)
        # frame
        cv.rect(0, (y0 + y1) / 2 + 2.5, x1 - x0 + 14, y1 - y0 + 15, _hex(WOOD[0]), 1.0)
        cv.rect(0, (y0 + y1) / 2, x1 - x0 + 12, y1 - y0 + 12, _hex(WOOD[1]), 1.0)
        cv.line(x0 - 6, y0 - 5.5, x1 + 6, y0 - 5.5, .9, _hex(WOOD[2]), 1.0)
        cv.line(x0 - 5.5, y0 - 6, x0 - 5.5, y1 + 6, .9, _hex(WOOD[2]), .8)
        for k in range(9):                                                             # wood grain
            yy = y0 - 4 + k * (y1 - y0 + 8) / 8
            cv.line(x1 + 3, yy, x1 + 3.5, yy + 6, .4, _hex(WOOD[0]), .7); cv.line(x0 - 3, yy + 3, x0 - 3.5, yy + 9, .4, _hex(WOOD[0]), .7)
        # slate with smudges of erased writing
        bd = pal.ramps.get("board", pal.ramps["bg"])
        m = (wx > x0) & (wx < x1) & (wy > y0) & (wy < y1)
        sm = vnoise(wx / 28.0 + 3, wy / 14.0, 4.2) * .7 + vnoise(wx / 7.0, wy / 5.0, 8.8) * .3
        t = np.clip(.15 + .75 * sm, 0, 1) * (len(bd) - 1); i = np.minimum(t.astype(int), len(bd) - 2); f = (t - i)[..., None]
        col = bd[i] * (1 - f) + bd[i + 1] * f
        streak = (np.abs(((wy - y0) * .6 + wx * .12) % 13 - 6.5) < .6) & (sm > .55)           # eraser sweeps
        col = np.where(streak[..., None], col * .8 + pal.ramp("body", .35) * .2, col)
        cv.rgb[m] = col[m]
        cv.glow(x0 + 30, y0 + 20, 70, pal.ramp("pale", .5), .05)
        # chalk tray, sticks, eraser
        cv.rect(0, y1 + 8.5, x1 - x0 + 18, 4.5, _hex(WOOD[2]), 1.0); cv.rect(0, y1 + 11, x1 - x0 + 18, 1.2, _hex(WOOD[0]), 1.0)
        for x, c, L in ((-52, "pale", 9), (-40, "energy", 6), (-31, "accent", 5), (58, "pale", 4)):
            cv.capsule(x, y1 + 6.2, x + L, y1 + 6.0, 1.1, flat=pal.ramp(c, .85 if c != "pale" else 1.0))
        cv.rect(30, y1 + 5.0, 18, 4.5, _hex("#5A1E18"), 1.0); cv.rect(30, y1 + 7.0, 18, 2.0, pal.ramp("pale", .55), 1.0)
        dy = y1 + 74
        cv.rect(0, dy + 40, 400, 80, _hex(WOOD[0]), 1.0); cv.rect(0, dy, 400, 5, _hex(WOOD[2]), 1.0); cv.rect(0, dy + 3.5, 400, 2, _hex(WOOD[1]), 1.0)
        for k, (c, w, hh) in enumerate((("#5A1E18", 30, 6), ("#6A5418", 26, 5), ("#5A3A22", 32, 5))):    # books
            yb = dy - 2.5 - sum(q[2] for q in ((0, 0, 6), (0, 0, 5), (0, 0, 5))[:k]) - hh / 2 + 2.5
            cv.rect(-52 + k * 2, yb, w, hh, _hex(c), 1.0); cv.line(-52 + k * 2 - w / 2 + 2, yb - hh / 2 + 1, -52 + k * 2 + w / 2 - 2, yb - hh / 2 + 1, .5, pal.ramp("pale", .4), .6)
        cv.line(58, dy - 1, 58, dy - 9, 1.0, _hex(WOOD[2]), 1.0); cv.ring(58, dy - 19, 11.5, .6, _hex("#8A5A32"), .9)  # globe
        cv.sphere(58, dy - 19, 10, ramp="dim", light=(-.5, -.6), tone=1.15)
        for a in (-.35, .1, .5): cv.ellipse(58 + 10 * a, dy - 19 - 2 * a, 3.5, 2.5, pal.ramp("energy", .45), .8, ang=a)

    def _calendar(self, cv, B, cal):
        pal = cv.pal; kind, b0, y_a, y_b, fb = cal
        nx, ny = -44.0, -24.0
        sw = 0.0
        if kind == "pin" and B < b0 + 1.2: sw = 8 * math.exp(-(B - b0) * 3) * math.sin((B - b0) * 9)    # swings in
        ca = math.radians(sw)
        def P(dx, dy):
            return (nx + dx * math.cos(ca) - dy * math.sin(ca), ny + dx * math.sin(ca) + dy * math.cos(ca))
        def quad(x0, y0, x1, y1, col, a=1.0):
            cv.poly([P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1)], col, a)
        cv.line(nx, ny - 6, nx, ny + 1, .8, pal.ramp("pale", .45), 1.0); cv.disc(nx, ny - 6, 1.2, _hex(WOOD[2]), 1.0)
        quad(-24, 1, 24, 41, pal.ramp("bg", .05), .5)                                     # shadow
        quad(-23, 0, 23, 39, pal.ramp("pale", .55))                                       # page stack edge
        years = [y_a]
        if kind == "flip":
            steps = [y_a + round((y_b - y_a) * k / 6) for k in range(7)]; years = steps
        # which year is on top + current flip progress
        if kind == "flip":
            u = min(max((B - b0) / max(fb, 1e-6), 0.0), 1.0) * 6
            k = int(min(u, 5.999)); f = u - k if u < 6 else 1.0
            under, top = (years[min(k + 1, 6)], years[k]) if u < 6 else (years[6], None)
        else:
            under, top, f = years[0], None, 0.0
        self._page(cv, P, quad, under, 1.0)
        if top is not None and f < 1:
            self._page(cv, P, quad, top, 1 - f, lift=f)
        quad(-23, 0, 23, 7, pal.ramp("accent", .45)); quad(-23, 5.5, 23, 7, pal.ramp("accent", .25))       # binding
        for hx in (-13, 13): cv.disc(*P(hx, 3.2), 1.3, pal.ramp("bg", .1), 1.0)
        from .minifont import draw_mini

    def _page(self, cv, P, quad, year, h, lift=0.0):
        """a calendar sheet; h<1 = being flipped up over the binding (foreshortened), lift tints its back."""
        pal = cv.pal; top, bot = 7.0, 7.0 + 31.0 * h
        quad(-22, top, 22, bot, pal.ramp("pale", 1.0 - .3 * lift))
        if h > .45:
            arr = _font(str(year)); dot = 1.55
            x, y = P(0, top + (bot - top) * .58)
            from .bitmap import Bitmap, draw_bitmap
            draw_bitmap(cv, Bitmap(np.kron(arr, np.ones((1, 1), bool)), x, y, dot), pal.ramp("bg", .1), 1.0)
            draw_bitmap(cv, Bitmap(mini_bitmap("YIL"), *P(0, top + 4.5), 1.0), pal.ramp("accent", .5), 1.0)
        quad(-22, bot - 1, 22, bot, pal.ramp("pale", .7))

    def _tag(self, cv, kind):
        pal = cv.pal; x, y = self.p["tag_xy"]
        if kind == "legible":
            before = cv.rgb.copy()
            draw_text(cv, self.handle, x, y, 1.0, pal.ramp("pale", 1.0), 1.0, snap=True)
            ch = np.abs(cv.rgb - before).max(-1) > 2e-3          # legible tag: no glow, no vignette (QC canli-gozu)
            cv.glowbuf[ch] = 0; cv.keep = ch if getattr(cv, "keep", None) is None else (cv.keep | ch)
        else:
            arr = _font(self.handle)
            chalk_blit(cv, arr, x, y, .55, pal.ramp("pale", .75), .45, 1.0, seed=11.0, slant=.02, wobble=.2, grain=.35)

    def _chalk_tip(self, cv, B, tip):
        x, y = tip; pal = cv.pal
        cv.capsule(x + 1.0, y - 1.0, x + 3.6, y - 6.0, .85, flat=pal.ramp("pale", 1.0))
        cv.capsule(x + 3.6, y - 6.0, x + 4.4, y - 7.6, .85, flat=pal.ramp("pale", .7))
        for k in range(3):
            a = B * 7.0 + k * 2.1; r = (B * 3.0 + k * .37) % 1.0
            cv.points(np.array([x + .5 + 2.5 * math.sin(a)]), np.array([y + 1 + 5 * r]), pal.ramp("pale", .85), .7 * (1 - r))

    def _puff(self, cv, age):
        if age < 0 or age > 1.6: return
        pal = cv.pal; rng = np.random.default_rng(31); n = 90
        a = rng.random(n) * TAU; v = rng.uniform(8, 30, n); k = 1 - math.exp(-age * 3.2)
        x = np.cos(a) * v * k; y = -55 + np.sin(a) * v * .55 * k + 6 * age * age
        cv.points(x, y, pal.ramp("pale", .9), np.clip(1 - age / 1.6, 0, 1) * rng.uniform(.4, 1, n), size=1)
        cv.glow(0, -55, 18 + 14 * k, pal.ramp("pale", .8), .25 * (1 - age / 1.6))

    def _dust(self, cv, B):
        pal = cv.pal; rng = np.random.default_rng(17); n = 46
        x0 = rng.uniform(-95, 95, n); sp = rng.uniform(1.5, 4, n); ph = rng.random(n)
        y = -120 + ((ph * 260 + B * sp * 2.2) % 260); x = x0 + 3 * np.sin(B * .7 + ph * 9)
        cv.points(x, y, pal.ramp("pale", .8), .18 + .25 * rng.random(n))


SCENES["chalk_unify"] = ChalkUnify

