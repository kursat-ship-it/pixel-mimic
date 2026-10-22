"""Depth layers: parallax backdrops (far), foreground particles (near), ambient shimmer.
Each layer draws with its own camera: zoom^par and pan×par, so far layers barely move and near layers move more
than the subject — the cheap trick that makes a flat pixel frame feel deep."""
import math
import numpy as np
from .raster import Camera
from .bitmap import draw_mark
from .pixfont import mark_layers

TAU = math.pi * 2


def with_par(cv, par, fn):
    c = cv.cam
    sub = Camera(c.cx * par, c.cy * par, c.zoom ** par, c.rot * min(1.0, par))
    keep = cv.cam; cv.set_cam(sub)
    try: fn()
    finally: cv.set_cam(keep)


class Layer:
    par = 0.2
    def __init__(self, seed, pal, **kw):
        self.r = np.random.default_rng(seed); self.pal = pal; self.kw = kw; self.setup()
    def setup(self): pass
    def draw(self, cv, t, lb): pass
    def render(self, cv, t, lb): with_par(cv, self.kw.get("par", self.par), lambda: self.draw(cv, t, lb))


class Stars(Layer):
    """3 depths of stars, twinkle, a few 4-point sparkles, and the hayret mark hidden as a faint constellation."""
    par = 0.12
    def setup(self):
        n = 320; self.x = self.r.uniform(-260, 260, n); self.y = self.r.uniform(-420, 420, n)
        self.d = self.r.choice([.4, .7, 1.0], n, p=[.55, .3, .15]); self.ph = self.r.random(n) * TAU
        self.sp = [(self.r.uniform(-90, 90), self.r.uniform(-160, 160), self.r.random() * TAU) for _ in range(5)]
        L = mark_layers(); ys, xs = np.nonzero(L["o"] | L["s"])
        self.cx, self.cy = 52 + (xs - 7) * 3.0, -118 + (ys - 5) * 3.0
    def draw(self, cv, t, lb):
        tw = .55 + .45 * np.sin(t * (1.5 + self.d * 2) + self.ph)
        for dval, rp in ((.4, .45), (.7, .7), (1.0, .95)):
            m = self.d == dval
            cv.points(self.x[m] * (1 + dval * .3), self.y[m] * (1 + dval * .3), self.pal.ramp("pale", rp), alpha=(tw[m] * dval).clip(0, 1))
        for x, y, ph in self.sp:
            k = max(0.0, math.sin(t * 1.3 + ph)) ** 3
            if k > .05:
                c = self.pal.ramp("energy", .9)
                cv.line(x - 3 * k, y, x + 3 * k, y, .8, c, k); cv.line(x, y - 3 * k, x, y + 3 * k, .8, c, k)
                cv.glow(x, y, 3, c, .4 * k)
        if self.kw.get("constellation", True):
            a = .35 + .25 * math.sin(t * .8)
            cv.points(self.cx, self.cy, self.pal.ramp("pale", .8), alpha=a)


class Nebula(Layer):
    """Soft dithered clouds of cobalt and turquoise light drifting slowly.
    kw: ramps / weights (e.g. drop "accent" behind pale line-art, whose additive coral light would tint it)."""
    par = 0.18
    def setup(self):
        ramps = self.kw.get("ramps", ["dim", "energy", "body", "accent"])
        dflt = {"dim": .35, "energy": .25, "body": .2, "accent": .2}
        w = np.asarray(self.kw.get("weights", [dflt.get(r_, .25) for r_ in ramps]), float)
        w = w / w.sum()
        self.b = [(self.r.uniform(-120, 120), self.r.uniform(-220, 220), self.r.uniform(45, 95),
                   self.r.choice(ramps, p=w), self.r.random() * TAU) for _ in range(6)]
    def draw(self, cv, t, lb):
        for x, y, r, ramp, ph in self.b:
            k = {"dim": .30, "energy": .20, "body": .24, "accent": .14}.get(ramp, .2)
            cv.glow(x + 12 * math.sin(t * .07 + ph), y + 8 * math.cos(t * .05 + ph), r, self.pal.ramp(ramp, .55), k)


class Tiles(Layer):
    """Faint İznik-style 8-point-star tile lattice (the channel's cultural signature), slowly breathing."""
    par = 0.08
    def draw(self, cv, t, lb):
        wx, wy = cv.world_grid(); P = self.kw.get("cell", 44.0)
        u = (wx / P) % 1.0 - .5; v = (wy / P) % 1.0 - .5
        r = .30 + .02 * math.sin(t * .6)
        sq = np.maximum(np.abs(u), np.abs(v)) < r; dm = (np.abs(u) + np.abs(v)) < r * 1.41
        star = sq | dm
        e = 1.0 / (P * cv.cam.zoom) * 1.2
        inner = (np.maximum(np.abs(u), np.abs(v)) < r - e) | ((np.abs(u) + np.abs(v)) < (r - e) * 1.41)
        edge = star & ~inner
        cv._blend((slice(None), slice(None)), edge.astype(np.float32) * self.kw.get("alpha", .38), cv._col(self.pal.ramp("dim", .7)))
        dots = (np.abs(np.abs(u) - .5) < e) & (np.abs(np.abs(v) - .5) < e)
        cv._blend((slice(None), slice(None)), dots.astype(np.float32) * .5, cv._col(self.pal.ramp("energy", .35)))


class Grid(Layer):
    """Retro perspective floor grid scrolling toward the viewer (screen-anchored)."""
    par = 0.0
    def draw(self, cv, t, lb):
        H, W = cv.H, cv.W; hz = H * .62
        ys, xs = cv.ys, cv.xs; below = ys > hz
        d = (ys - hz) / (H - hz + 1e-6) + 1e-3; z = 1.0 / d
        gx = ((xs - W / 2) * z / 40.0) % 1.0; gz = (z * .9 + t * .9) % 1.0
        w = .06 + .02 * d
        line = below & ((np.abs(gx - .5) > .5 - w) | (gz < w * 1.4))
        fade = np.clip(d * 1.6, 0, 1)
        cv._blend((slice(None), slice(None)), line.astype(np.float32) * fade * .55, cv._col(self.pal.ramp("body", .45)))
        cv.glow(0 + cv.cam.cx, (hz - H / 2) / cv.cam.zoom + cv.cam.cy, 60 / cv.cam.zoom, self.pal.ramp("energy", .5), .25)


class Skyline(Layer):
    """Two rows of city silhouettes with blinking windows and coral antenna beacons."""
    par = 0.25
    def setup(self):
        self.rows = []
        for depth, (y0, hmin, hmax) in enumerate([(150, 30, 90), (175, 20, 60)]):
            x = -300.0; bl = []
            while x < 300:
                w = self.r.uniform(14, 30); h = self.r.uniform(hmin, hmax)
                win = [(self.r.uniform(2, w - 2), self.r.uniform(3, h - 3), self.r.random()) for _ in range(int(w * h / 90))]
                bl.append((x, w, h, win, self.r.random() < .25)); x += w + self.r.uniform(1, 5)
            self.rows.append((y0, depth, bl))
    def draw(self, cv, t, lb):
        for y0, depth, bl in self.rows:
            body = self.pal.ramp("bg", .55 + .35 * depth)
            for x, w, h, win, ant in bl:
                cv.capsule(x + w / 2, y0 - h + w / 2, x + w / 2, y0 + 200, w / 2, flat=body)
                for wx, wy, ph in win:
                    on = math.sin(t * .4 + ph * 40) > .2
                    if on: cv.disc(x + wx, y0 - h + wy, .6, self.pal.ramp("energy" if ph < .3 else "pale", .6 + .3 * depth), .85)
                if ant:
                    cv.line(x + w / 2, y0 - h, x + w / 2, y0 - h - 8, .7, body)
                    k = 1.0 if (t * 1.2 + x * .01) % 1.0 < .25 else .15
                    cv.disc(x + w / 2, y0 - h - 8, .9, self.pal.ramp("accent", .55), k); cv.glow(x + w / 2, y0 - h - 8, 3, self.pal.ramp("accent", .5), .4 * k)
    def roof(self, i=None):
        """A tall building top in the near row (anchor for billboards / neon signs) in layer coords."""
        y0, _, bl = self.rows[0]
        cand = sorted([b for b in bl if -40 < b[0] < 40], key=lambda b: -b[2]) or bl
        x, w, h = cand[0][:3]; return x + w / 2, y0 - h


class Horizon(Layer):
    """Low glowing band (turquoise core, coral fringe) that gives every frame a light source and depth."""
    par = 0.1
    def draw(self, cv, t, lb):
        y = self.kw.get("y", 150); k = self.kw.get("k", 1.0)
        for i, x in enumerate((-90, 0, 90)):
            cv.glow(x + 10 * math.sin(t * .1 + i), y, 85, self.pal.ramp("energy", .55), .22 * k)
        cv.glow(-60, y + 30, 70, self.pal.ramp("accent", .5), .12 * k)
        cv.glow(70, y + 40, 60, self.pal.ramp("accent", .45), .10 * k)
        cv.glow(0, -y - 40, 120, self.pal.ramp("body", .45), .14 * k)


class Rays(Layer):
    """Slowly turning dithered light rays from a point (reveals, 'wonder' moments)."""
    par = 0.3
    def draw(self, cv, t, lb):
        wx, wy = cv.world_grid(); cx, cy = self.kw.get("x", 0), self.kw.get("y", 0)
        a = np.arctan2(wy - cy, wx - cx); r = np.hypot(wx - cx, wy - cy)
        n = self.kw.get("n", 9)
        m = (np.sin(a * n + t * .25) > .55).astype(np.float32) * np.clip(1 - r / 260, 0, 1) * .5
        cv.glowbuf += m[..., None] * np.asarray(self.pal.ramp("energy", .55)) * .35


class Bokeh(Layer):
    """Near, out-of-focus dithered discs drifting faster than the subject.
    kw: n (count), ramps (palette ramps to pick from), weights (pick probabilities)."""
    par = 1.6
    def setup(self):
        ramps = self.kw.get("ramps", ["pale", "energy", "accent"])
        w = np.asarray(self.kw.get("weights", [.4, .35, .25][:len(ramps)] if len(ramps) <= 3 else [1] * len(ramps)), float)
        w = w / w.sum()
        self.b = [(self.r.uniform(-120, 120), self.r.uniform(-200, 200), self.r.uniform(7, 20), self.r.choice(ramps, p=w),
                   self.r.random() * TAU, self.r.uniform(.4, 1)) for _ in range(self.kw.get("n", 7))]
    def draw(self, cv, t, lb):
        for x, y, r, ramp, ph, sp in self.b:
            X = ((x + t * 6 * sp + 150) % 300) - 150; Y = y + 10 * math.sin(t * .3 * sp + ph)
            cv.disc(X, Y, r, self.pal.ramp(ramp, .6), .2)
            cv.ring(X, Y, r - .5, 1, self.pal.ramp(ramp, .85), .2)
            cv.glow(X, Y, r * .8, self.pal.ramp(ramp, .6), .06)


class Debris(Layer):
    """Small fast near particles (sparks / dust chunks) with short streaks."""
    par = 1.35
    def setup(self):
        n = self.kw.get("n", 36)
        self.x, self.y = self.r.uniform(-120, 120, n), self.r.uniform(-220, 220, n)
        self.v = self.r.uniform(8, 26, n); self.c = self.r.random(n)
    def draw(self, cv, t, lb):
        X = ((self.x + t * self.v * .6 + 140) % 280) - 140; Y = ((self.y + t * self.v + 230) % 460) - 230
        for i in range(len(X)):
            col = self.pal.ramp("energy" if self.c[i] < .4 else "pale", .7)
            cv.line(X[i], Y[i], X[i] - self.v[i] * .05, Y[i] - self.v[i] * .09, .9, col, .75)


class Pollen(Layer):
    """Sunlit pollen / seed fluff: slow drifting 1-px motes in two depths with a gentle sine sway (meadows, gardens).
    kw: n, ramps (default pale + energy)."""
    par = 1.15
    def setup(self):
        n = self.kw.get("n", 46)
        self.x, self.y = self.r.uniform(-1, 1, n), self.r.uniform(-1, 1, n)
        self.d = self.r.choice([.5, 1.0], n, p=[.6, .4]); self.ph = self.r.random(n) * TAU
        self.c = self.r.random(n)
    def draw(self, cv, t, lb):
        X = ((self.x * 150 + t * 2.2 * self.d + 6 * np.sin(t * .6 + self.ph)) % 300 - 150) / cv.cam.zoom ** .3 + cv.cam.cx
        Y = ((self.y * 260 - t * .9 * self.d + 3 * np.sin(t * .9 + self.ph * 2)) % 520 - 260) / cv.cam.zoom ** .3 + cv.cam.cy
        ramps = self.kw.get("ramps", ["pale", "energy"])
        col = np.where((self.c < .55)[:, None], self.pal.ramp(ramps[0], .9), self.pal.ramp(ramps[-1], .85))
        cv.points(X, Y, col, alpha=.75 * self.d)


class Dust(Layer):
    par = 1.0
    def setup(self):
        n = 120; self.x, self.y = self.r.uniform(-1, 1, n), self.r.uniform(-1, 1, n); self.d = self.r.uniform(.3, 1, n); self.ph = self.r.random(n)
    def draw(self, cv, t, lb):
        X = ((self.x * 140 + t * 1.5 * self.d) % 280 - 140) / cv.cam.zoom ** .3 + cv.cam.cx
        Y = ((self.y * 240 - t * 3 * self.d) % 480 - 240) / cv.cam.zoom ** .3 + cv.cam.cy
        tw = .35 + .65 * (np.sin(t * 2 + self.ph * 6.28) > .6)
        cv.points(X, Y, self.pal.ramp("pale", .6), alpha=.5 * tw * self.d)


LAYERS = {"pollen": Pollen, "horizon": Horizon, "stars": Stars, "nebula": Nebula, "tiles": Tiles, "grid": Grid, "skyline": Skyline, "rays": Rays,
          "bokeh": Bokeh, "debris": Debris, "dust": Dust}

# default depth stack per scene (hayret visual grammar: ≥ 3 moving layers everywhere)
DEFAULT_STACK = {
    "hero": (["horizon", "nebula", "stars", "tiles"], ["bokeh", "dust"]),
    "lattice": (["horizon", "nebula", "tiles"], ["debris", "bokeh"]),
    "chain": (["horizon", "nebula", "stars", "grid"], ["bokeh", "dust"]),
    "streaks": (["horizon", "nebula", "stars"], ["debris", "dust"]),
    "pod": (["horizon", "nebula", "tiles"], ["bokeh", "dust"]),
    "junction": (["horizon", "nebula", "stars"], ["bokeh", "debris"]),
    "network": (["horizon", "nebula", "stars"], ["bokeh", "debris"]),
    "silhouette": (["horizon", "nebula", "rays", "stars"], ["bokeh", "dust"]),
    "object": (["horizon", "nebula", "stars", "skyline"], ["bokeh", "dust"]),
    "image": (["horizon", "nebula", "stars", "tiles"], ["bokeh", "dust"]),
    "void": (["horizon", "nebula", "stars", "tiles"], ["bokeh", "dust"]),
    "pendulum_grid": (["horizon", "nebula", "stars"], ["bokeh", "dust"]),
    "formula_scope": (["grid", "nebula"], ["dust"]),
    "chladni": (["horizon", "nebula"], ["dust"]),
}


def scanline_shimmer(rgb, phase, strength=.06):
    """A soft bright band rolling down the frame (phase 0..1) + faint alternate-row darkening (CRT shimmer)."""
    H = rgb.shape[0]; y = np.arange(H, dtype=np.float32)
    pos = (phase % 1.0) * (H + 60) - 30
    band = 1 + strength * np.exp(-((y - pos) / 10) ** 2)
    rows = np.where(y % 2 == 0, 1.0, 0.975)
    rgb *= (band * rows)[:, None, None]
    return rgb
