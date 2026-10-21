"""Fractal scenes (reusable): a growing Koch snowflake and a deep, beat-synced Mandelbrot zoom (numpy, art resolution,
4×4 Bayer-dithered palette bands with chiptune colour cycling)."""
import math
import numpy as np
from .scenes import Scene, ease, pulse, TAU
from .palette import BAYER4, _hex
from .bitmap import Bitmap, draw_bitmap
from .scenes_music import EIGHTH, _sprite


def koch_points(level, growth=1.0, R=60.0, cx=0.0, cy=0.0, rot=0.0):
    """Closed Koch snowflake polygon (list of (x, y)); the newest level's bumps grow out by `growth` ∈ [0, 1].
    Returns (points, indices of the newest peak vertices)."""
    pts = [(cx + R * math.cos(rot - math.pi / 2 + k * TAU / 3), cy + R * math.sin(rot - math.pi / 2 + k * TAU / 3)) for k in range(3)]
    new = []
    for lv in range(level):
        g = growth if lv == level - 1 else 1.0
        out = []; new = []
        n = len(pts)
        for i in range(n):
            (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
            dx, dy = bx - ax, by - ay
            p1 = (ax + dx / 3, ay + dy / 3); p3 = (ax + 2 * dx / 3, ay + 2 * dy / 3)
            mx, my = (ax + bx) / 2, (ay + by) / 2
            L = math.hypot(dx, dy); nx, ny = dy / L, -dx / L                   # outward for clockwise-in-screen order
            h = L * math.sqrt(3) / 6 * g
            out += [(ax, ay), p1, (mx + nx * h, my + ny * h), p3]; new.append(len(out) - 2)
        pts = out
    return pts, new


class Koch(Scene):
    """Koch snowflake gaining one iteration every `step_every` beats (iter_from → iter_to); new bumps grow out over a
    third of a beat, new vertices spark turquoise; faint larger/smaller echo flakes counter-rotate behind (self-
    similarity), tiny ♪ glyphs ride the perimeter, a dithered inner glow breathes on the beat. tick SFX per step."""
    defaults = {"kind": "snowflake", "iter_from": 0, "iter_to": 4, "step_every": 1.0, "spark_notes": True,
                "inner_glow": True, "R": 62.0, "x": 0.0, "y": 22.0, "grow": .33, "echoes": True}

    def focus(self, lb, dur_b): return (self.p["x"], self.p["y"])

    def _level(self, lb):
        p = self.p; st = max(0.0, lb) / p["step_every"]; k = int(math.floor(st))
        lv = min(p["iter_to"], p["iter_from"] + k)
        g = 1.0 if (k == 0 or lv >= p["iter_to"] and p["iter_from"] + k > p["iter_to"]) else ease(min(1, (st - k) / p["grow"]), "outCubic")
        return lv, g, st - k

    def draw(self, cv, lt, lb, dur_b):
        p, E, A, pal = self.p, self.E, self.A, self.pal
        lv, g, fr = self._level(lb)
        cx, cy, R = p["x"], p["y"], p["R"]
        bp = pulse(lb, 1.0, 4.0)
        if p["echoes"]:
            for sc_, al, sp in ((1.75, .22, -.05), (1.38, .35, .08)):
                pts, _ = koch_points(max(0, lv - 1), 1.0, R * sc_, cx, cy, rot=lt * sp)
                cv.poly_outline(pts, pal.ramp("body", .55), al)
        if p["inner_glow"]:
            cv.glow(cx, cy, R * .9, E(.45), .25 + .2 * bp)
        pts, new = koch_points(lv, g, R, cx, cy)
        cv.poly(pts, pal.ramp("dim", .35), .9)
        cv.glow(cx, cy, R * .55, E(.6), .22 + .25 * bp)
        inner, _ = koch_points(max(0, lv - 1), 1.0, R * .36, cx, cy, rot=-lt * .3 + math.pi)
        cv.poly_outline(inner, E(.75), .7)
        cv.poly_outline(pts, pal.ramp("pale", 1.0), 1.0)
        # sparks on the newest vertices
        if lv > p["iter_from"] and fr < .25 / p["step_every"] * 1.0 + .25:
            k = 1 - min(1, fr / .3)
            sel = new if len(new) <= 64 else new[::max(1, len(new) // 64)]
            for i in sel:
                x, y = pts[i]; cv.glow(x, y, 3.5, E(.95), .8 * k)
            cv.points([pts[i][0] for i in new], [pts[i][1] for i in new], E(1.0), alpha=k)
        # notes riding the perimeter
        if p["spark_notes"]:
            P = np.asarray(pts + pts[:1]); seg = np.hypot(*(P[1:] - P[:-1]).T); cum = np.concatenate([[0], np.cumsum(seg)])
            for j in range(5):
                u = ((j / 5 + lt * .045 * (1 + .3 * (j % 2))) % 1.0) * cum[-1]
                i = int(np.searchsorted(cum, u) - 1); i = max(0, min(i, len(seg) - 1)); f = (u - cum[i]) / max(seg[i], 1e-6)
                x, y = P[i] + (P[i + 1] - P[i]) * f
                cv.glow(x, y, 5, E(.8), .5)
                draw_bitmap(cv, Bitmap(EIGHTH, x, y - 3, 1.0), pal.ramp("pale", 1.0) if j % 2 else E(1.0))

    def sfx(self, dur_b):
        p = self.p; out = []
        for k in range(1, p["iter_to"] - p["iter_from"] + 1):
            b = k * p["step_every"]
            if b < dur_b: out.append((b, "tick"))
        return out


# ------------------------------------------------------------------ Mandelbrot
BANDS = ["#0B1230", "#141E4A", "#1E2E73", "#2C47A6", "#4169D1", "#0B4F5C", "#13A39B", "#41E8D2", "#D2FFF5"]


def mandel(c, max_iter, bail=256.0):
    """Escape-time Mandelbrot on a complex array → smooth iteration count μ (nan = interior). float64, active-set loop."""
    shape = c.shape; c = c.ravel(); z = np.zeros_like(c); mu = np.full(c.shape, np.nan)
    idx = np.arange(c.size); cc = c.copy()
    # cheap interior tests: main cardioid + period-2 bulb
    x, y = cc.real, cc.imag; q = (x - .25) ** 2 + y * y
    inside = (q * (q + (x - .25)) <= .25 * y * y) | ((x + 1) ** 2 + y * y <= 1 / 16)
    idx, cc, z = idx[~inside], cc[~inside], z[~inside]
    for n in range(max_iter):
        z = z * z + cc
        a2 = z.real * z.real + z.imag * z.imag
        esc = a2 > bail
        if esc.any():
            ze = a2[esc]
            mu[idx[esc]] = n + 1 - np.log2(np.log(np.sqrt(ze)) / math.log(2) + 1e-12)
            keep = ~esc; idx, cc, z = idx[keep], cc[keep], z[keep]
            if not idx.size: break
    return mu.reshape(shape)


class MandelZoom(Scene):
    """Deep zoom into the Mandelbrot set (default: seahorse valley) at art resolution: zoom ×zoom_per_beat per beat,
    smooth-iteration bands on the Çini Gecesi ramps (far = deep lapis, near the boundary = firuze → türkuaz → parıltı,
    interior = gece, rare coral sparkles), 4×4 Bayer dither between bands, palette cycling one step per beat
    (band_on_beat). The outermost band stays transparent so the depth layers show through. note_emitters: streams of
    tiny note glyphs fly out of the boundary at the music's speeds (16th, 8th, quarter, whole)."""
    defaults = {"center": [-0.743643887037151, 0.131825904205330], "zoom_start": 1.0, "zoom_per_beat": 1.6,
                "max_iter": 96, "iter_per_octave": 14, "width": 0.9, "band_on_beat": True, "note_emitters": 4,
                "emit_rates": [4, 2, 1, .25], "emit_speeds": [70, 48, 32, 18], "transparent_far": .12, "cycle": .25,
                "shockwave": True, "adapt_bands": True, "floor_pct": 6.0, "floor_keep": 4.0}

    def setup(self):
        self.cols = np.array([_hex(h) for h in BANDS], np.float32)

    def focus(self, lb, dur_b): return (0.0, 0.0)

    def draw(self, cv, lt, lb, dur_b):
        p, E, A, pal = self.p, self.E, self.A, self.pal
        Z = p["zoom_start"] * p["zoom_per_beat"] ** max(0.0, lb)
        k = p["width"] / 180.0 / Z
        wx, wy = cv.world_grid()
        c = (p["center"][0] + wx.astype(np.float64) * k) + 1j * (p["center"][1] - wy.astype(np.float64) * k)
        mi = int(p["max_iter"] + p["iter_per_octave"] * math.log2(max(Z, 1)))
        mu = mandel(c, mi)
        interior = np.isnan(mu)
        m = np.where(interior, 0, mu)
        # deep in the zoom every visible pixel escapes late, so a fixed scale pushed the whole frame into the top
        # (türkuaz) bands = a flat, soft wall. Measure escape depth from this frame's own floor (low percentile of the
        # escaping pixels) so the far → near band contrast survives the whole dive (no-op near zoom 1).
        esc = m[~interior]
        floor_ = max(0.0, float(np.percentile(esc, p["floor_pct"])) - p["floor_keep"]) if (p["adapt_bands"] and esc.size) else 0.0
        mr = np.maximum(m - floor_, 0)
        t = np.clip(np.log1p(mr) / math.log1p(max(mi * .55 - floor_, 8.0)), 0, 1)   # proximity to the set
        cyc = (math.floor(lb) if p["band_on_beat"] else lb) * p["cycle"]
        tri = np.abs(((m * .18 + cyc) % 1.0) - .5) * 2                              # moving contour bands
        nb = len(self.cols)
        f = t * (nb - 1) * 1.05 - .35 + .9 * tri
        by = np.tile(BAYER4, (cv.H // 4 + 1, cv.W // 4 + 1))[:cv.H, :cv.W]
        idx = np.clip(np.floor(f + by), 0, nb - 1).astype(int)
        col = self.cols[idx]
        paint = (~interior) & (t > p["transparent_far"])
        a = np.clip((t - p["transparent_far"]) / .08, 0, 1)
        a = (by < a).astype(np.float32)                                              # dithered edge into the sky
        mask = (paint.astype(np.float32) * a)[..., None]
        cv.rgb[:] = cv.rgb * (1 - mask) + col * mask
        gece = np.array(_hex("#060814"), np.float32)
        cv.rgb[interior] = gece
        # interior rim light (one px inside the set), coral sparkles on the outer bands
        edge = interior & ~(np.roll(interior, 1, 0) & np.roll(interior, -1, 0) & np.roll(interior, 1, 1) & np.roll(interior, -1, 1))
        cv.rgb[edge] = np.array(_hex("#41E8D2"), np.float32) * .55 + gece * .45
        h = (np.arange(cv.H)[:, None] * 73856093 ^ np.arange(cv.W)[None, :] * 19349663 ^ int(math.floor(lb * 4)) * 83492791) % 1000
        spark = paint & (idx <= 2) & (h < 6)
        cv.rgb[spark] = np.array(_hex("#FF9A86"), np.float32)
        hot = (idx >= nb - 2) & paint
        cv.glowbuf[hot] += E(.8) * .12
        # drop shockwave
        if p["shockwave"] and lb < 1.6:
            q = lb / 1.6
            cv.ring(0, 0, 10 + 120 * ease(q, "outCubic"), 2.5 * (1 - q) + .6, E(1.0), 1 - q)
        # note emitters: 4 voices, 4 speeds, one onset grid
        gb = self.gbeat(lb)
        for s_i in range(min(p["note_emitters"], len(p["emit_rates"]))):
            r = p["emit_rates"][s_i]; v = p["emit_speeds"][s_i]
            col_s = [E(1.0), A(.72), pal.ramp("pale", .75), pal.ramp("pale", 1.0)][s_i % 4]
            life = 190 / v
            n_hi = math.floor(gb * r); n_lo = math.floor((gb - life) * r)
            for n in range(n_lo, n_hi + 1):
                tb = n / r; age = gb - tb
                if age < 0 or age > life or tb < self.b0 - .01: continue
                ang = ((n * 2654435761 + s_i * 97) % 3600) / 3600 * TAU
                d = 6 + age * v
                x, y = math.cos(ang) * d, math.sin(ang) * d * 1.2
                dot = [.9, 1.1, 1.4, 1.9][s_i % 4]
                if age < .15: cv.glow(x, y, 6, col_s, 1 - age / .15)
                if s_i == 3:
                    cv.ellipse(x, y, 3 * dot, 2.2 * dot, col_s, .95); cv.ellipse(x, y, 1.4 * dot, 1.2 * dot, pal.ramp("bg", .2), 1)
                elif s_i == 2:
                    cv.ellipse(x, y, 2.6, 1.9, col_s, 1, ang=-.35); cv.line(x + 2.2, y, x + 2.2, y - 9, .9, col_s)
                else:
                    draw_bitmap(cv, Bitmap(EIGHTH, x, y, dot), col_s)

    def sfx(self, dur_b): return []


from .scenes import SCENES  # noqa: E402
SCENES.update({"koch": Koch, "mandel_zoom": MandelZoom})
