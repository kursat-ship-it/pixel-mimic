"""Generic scene library. Each scene is a topic-agnostic motif from the recipe (hero, macro lattice, hopping chain,
perspective streaks, pod, junction/build, burst/network, silhouette, metaphor object, user image, void).
Scenes draw in WORLD units (≈ art pixels at zoom 1, origin = frame centre, y down) as pure functions of local time.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .shapes import Mask, load_mask, font_path

TAU = math.pi * 2


def ease(k, kind="inOutSine"):
    k = min(max(k, 0.0), 1.0)
    if kind == "linear": return k
    if kind == "inOutSine": return 0.5 - 0.5 * math.cos(math.pi * k)
    if kind == "outCubic": return 1 - (1 - k) ** 3
    if kind == "inCubic": return k ** 3
    if kind == "inOutCubic": return 4 * k ** 3 if k < .5 else 1 - (-2 * k + 2) ** 3 / 2
    if kind == "outExpo": return 1 if k >= 1 else 1 - 2 ** (-10 * k)
    if kind == "inExpo": return 0 if k <= 0 else 2 ** (10 * k - 10)
    return k


def pulse(lb, every=1.0, decay=4.0):
    """1 on each beat grid point, decaying."""
    return math.exp(-((lb % every) / every) * decay)


class Scene:
    defaults = {}
    sfx_default = []          # [(beat, kind)] relative to segment start (negative = from end)

    def __init__(self, params, seed, pal, base_dir="."):
        self.p = {**self.defaults, **(params or {})}
        self.rng = np.random.default_rng(seed)
        self.pal, self.base_dir = pal, base_dir
        self.E = lambda t: pal.ramp("energy", t)
        self.A = lambda t: pal.ramp("accent", t)
        self.setup()

    def setup(self): pass

    def bind(self, seg, spec):
        """Timeline context (global beat of the segment start, film length, loop) for scenes that follow the global
        beat grid (series notation, music-synced emitters). Called by the renderer and the validator."""
        self.b0 = float(seg.get("start_beat", 0.0)); self.dur = float(seg.get("end_beat", 0.0)) - self.b0
        self.total = float(spec.get("total_beats", 0.0)); self.loop = bool(spec.get("loop"))
        self.bpm = float(spec.get("music", {}).get("bpm", 120)); self.on_bind()
        return self

    def on_bind(self): pass
    b0, dur, total, loop, bpm = 0.0, 0.0, 0.0, False, 120.0

    def gbeat(self, lb):
        """Global beat for local beat lb."""
        return self.b0 + lb

    def draw(self, cv, lt, lb, dur_b): raise NotImplementedError
    def focus(self, lb, dur_b): return (0.0, 0.0)
    def sfx(self, dur_b): return list(self.sfx_default)


# ---------------------------------------------------------------- helpers
def branch_tree(rng, x, y, ang, length, r, depth, out, spread=0.5):
    n = 5; pts = [(x, y)]
    a = ang
    for i in range(n):
        a += rng.normal(0, 0.18)
        x += math.cos(a) * length / n; y += math.sin(a) * length / n; pts.append((x, y))
    out.append((pts, r))
    if depth > 0:
        for s in (-1, 1):
            if rng.random() < 0.8:
                branch_tree(rng, x, y, a + s * spread * (0.6 + rng.random() * .6), length * .62, r * .62, depth - 1, out, spread)


def draw_tree(cv, branches, ramp="body", tone=1.0, lit=0.0, E=None):
    for pts, r in branches:
        cv.polyline(pts, max(r, .6), ramp=ramp, tone=tone)
        if lit > 0.02 and E is not None:
            for (x, y) in pts[1::2]:
                cv.glow(x, y, r * 2.5, E(.8), lit * .25)


def text_mask(text, px=None):
    from .pixfont import text_mask as _tm
    from .captions import upper
    return _tm(upper(text))


class RectMask:
    def __init__(self, arr, x, y, h):
        self.a, self.x, self.y, self.h = arr, x, y, h
        self.ah, self.aw = arr.shape; self.w = h * self.aw / self.ah

    def test(self, wx, wy):
        u = ((wx - self.x) / self.w + .5) * self.aw; v = ((wy - self.y) / self.h + .5) * self.ah
        ok = (u >= 0) & (u < self.aw) & (v >= 0) & (v < self.ah)
        return ok & self.a[np.clip(v.astype(int), 0, self.ah - 1), np.clip(u.astype(int), 0, self.aw - 1)]


# ---------------------------------------------------------------- scenes
class Hero(Scene):
    """The ONE protagonist in action: shaded body + branches + a segmented tail, energy pulse on the beat,
    optional oscilloscope trace (data cue). Good for the HOOK and the LOOP target."""
    defaults = {"branches": 7, "tail": True, "trace": True, "body_r": 17, "x": -5, "y": -25, "pulse_every": 2}

    def setup(self):
        p, r = self.p, self.rng
        self.bx, self.by, self.br = p["x"], p["y"], p["body_r"]
        self.br_list = []
        for i in range(p["branches"]):
            a = -math.pi / 2 + (i / max(1, p["branches"] - 1) - .5) * math.pi * 1.5 + r.normal(0, .12)
            branch_tree(r, self.bx + math.cos(a) * self.br * .8, self.by + math.sin(a) * self.br * .8, a,
                        30 + r.random() * 20, 2.8, 2, self.br_list)
        self.tail_dir = math.radians(62)
        self.hill = (self.bx + math.cos(self.tail_dir) * self.br, self.by + math.sin(self.tail_dir) * self.br)

    def focus(self, lb, dur_b): return self.hill

    def draw(self, cv, lt, lb, dur_b):
        p, E = self.p, self.E
        if p["tail"]:
            hx, hy = self.hill; L, gap = 15, 3.5
            for k in range(14):
                s0, s1 = 4 + k * (L + gap), 4 + k * (L + gap) + L
                cv.capsule(hx + math.cos(self.tail_dir) * s0, hy + math.sin(self.tail_dir) * s0,
                           hx + math.cos(self.tail_dir) * s1, hy + math.sin(self.tail_dir) * s1, 3.2, ramp="pale")
            # travelling spark down the tail (one hop per 8th note)
            k = int(lb * 2) % 14; s = 4 + k * (L + gap) - gap / 2
            cv.glow(hx + math.cos(self.tail_dir) * s, hy + math.sin(self.tail_dir) * s, 5, E(.85), .9)
        draw_tree(cv, self.br_list, "body")
        cv.sphere(self.bx, self.by, self.br, "body", rim=E(.6))
        pk = pulse(lb, p["pulse_every"], 3.0)
        cv.glow(*self.hill, 9 + 4 * pk, E(.9), .8 + .9 * pk)
        cv.disc(*self.hill, 2.2, E(1.0))
        if p["trace"]:   # oscilloscope cue, screen-anchored world strip under the hero
            y0 = self.by + 95; xs = np.linspace(-80, 80, 90)
            ph = (lb / p["pulse_every"]) % 1.0
            ys = []
            for x in xs:
                u = ((x + 80) / 160 - ph) % 1.0
                spike = math.exp(-((u - .5) * 40) ** 2) * 14 - math.exp(-((u - .53) * 30) ** 2) * 4
                ys.append(y0 - spike)
            cv.polyline(list(zip(xs, ys)), .5, flat=E(.55))


class Lattice(Scene):
    """Macro texture: a band of shaded spheres (membrane / crystal / cells); energy particles flood through at `flood_at`."""
    defaults = {"r": 7.0, "flood_at": 2.0, "particles": 140, "rows": 2}

    def setup(self):
        r = self.rng
        self.cols = np.arange(-260, 261, self.p["r"] * 1.7)
        self.jit = r.normal(0, .8, (self.p["rows"], len(self.cols)))
        n = self.p["particles"]
        self.px, self.py0 = r.uniform(-120, 120, n), r.uniform(-170, -30, n)
        self.pv = r.uniform(.6, 1.4, n)

    def draw(self, cv, lt, lb, dur_b):
        R, E = self.p["r"], self.E
        fl = max(0.0, lb - self.p["flood_at"])
        cv.glow(0, 90, 110, E(.55), min(.55, fl * .18))
        # particles: drift, then rush down through the band
        y = self.py0 + 6 * np.sin(lt + self.px) + fl * 85 * self.pv
        cv.points(self.px + 2 * np.sin(lt * 1.3 + self.py0), y, E(.85), alpha=.9)
        for i in range(self.p["rows"]):
            yy = (i - (self.p["rows"] - 1) / 2) * R * 1.5
            for j, x in enumerate(self.cols):
                cv.sphere(x, yy + self.jit[i, j] + math.sin(lt * 2 + j) * .6, R, "body", rim=E(.5) if fl > 0 else None)
        for s in (-1, 1):
            heads = np.arange(-260, 261, 5.0)
            for x in heads:
                cv.sphere(x, s * (R * 1.5 + 3), 2.2, "pale", spec=False)
        if fl > 0:  # bright inflow points in the band
            for x in self.cols[::5]:
                cv.glow(x, 0, 6, E(.8), .5 * pulse(lb, .5, 3))

    def sfx(self, dur_b): return [(self.p["flood_at"], "whoosh")]


class Chain(Scene):
    """Rows of capsules (myelin / railway / pipeline) at several depths; a spark hops gap-to-gap on every 8th note."""
    defaults = {"len": 22.0, "gap": 4.0, "r": 3.2, "hop_every": 0.5, "rows": [[-70, .6], [-25, .8], [0, 1.0], [45, 1.5], [110, 2.4]]}

    def focus(self, lb, dur_b):
        k = int(lb / self.p["hop_every"]); L = self.p["len"] + self.p["gap"]
        return ((k % 16) * L - 8 * L, 0.0)

    def draw(self, cv, lt, lb, dur_b):
        p, E = self.p, self.E
        for y, s in sorted(p["rows"], key=lambda r: r[1]):
            L, g, r = p["len"] * s, p["gap"] * s, p["r"] * s
            main = abs(s - 1.0) < 1e-6
            off = (lt * 3 * s) % (L + g) if not main else 0
            for k in range(-14, 15):
                x0 = k * (L + g) - off
                cv.capsule(x0, y, x0 + L, y, r, ramp="pale" if main else "dim", tone=1.0 if main else .8)
                if not main and (k * 7 + int(lb * 2)) % 9 == 0:
                    cv.glow(x0 - g / 2, y, 3 * s, self.E(.7), .35)
            if main:
                cv.line(-400, y, 400, y, 1.0, self.pal.ramp("dim", .6), .6)
        x, y = self.focus(lb, dur_b)
        k = pulse(lb, p["hop_every"], 4)
        cv.glow(x - p["gap"] / 2, y, 6, E(.9), .7 + .8 * k)
        cv.disc(x - p["gap"] / 2, y, 1.5, E(1))


class Streaks(Scene):
    """Perspective lanes converging to a vanishing point with sparks racing along them (speed / scale)."""
    defaults = {"lanes": 6, "speed": 0.5, "vp": [70, -200]}

    def setup(self):
        self.starts = [(-150 + i * 55 + self.rng.normal(0, 8), 220) for i in range(self.p["lanes"])]
        self.phase = self.rng.random(self.p["lanes"])

    def focus(self, lb, dur_b): return tuple(self.p["vp"])

    def draw(self, cv, lt, lb, dur_b):
        vx, vy = self.p["vp"]; E = self.E
        for i, (sx, sy) in enumerate(self.starts):
            for k in range(26):
                u0 = 1 - 1 / (1 + k * .32); u1 = 1 - 1 / (1 + (k + .8) * .32)
                ax, ay = sx + (vx - sx) * u0, sy + (vy - sy) * u0
                bx, by = sx + (vx - sx) * u1, sy + (vy - sy) * u1
                cv.capsule(ax, ay, bx, by, 4.2 * (1 - u0) + .5, ramp="pale", tone=1 - u0 * .5)
            u = (lb * self.p["speed"] + self.phase[i]) % 1.0
            u = 1 - (1 - u) ** 2
            cv.glow(sx + (vx - sx) * u, sy + (vy - sy) * u, 6 * (1 - u) + 1.5, E(.85), 1.0)


class Pod(Scene):
    """A big shaded container full of small spheres (terminal / cell / seed); releases dots across a gap."""
    defaults = {"count": 13, "release_at": 1.0, "x": -12, "y": 15, "r": 42}

    def setup(self):
        p, r = self.p, self.rng; self.ves = []
        while len(self.ves) < p["count"]:
            a, d = r.random() * TAU, r.random() ** .5 * p["r"] * .7
            x, y = p["x"] + math.cos(a) * d, p["y"] + math.sin(a) * d
            if all(math.hypot(x - u, y - v) > 12 for u, v in self.ves): self.ves.append((x, y))
        self.dots = r.random((40, 3))

    def focus(self, lb, dur_b): return (self.p["x"] + self.p["r"], self.p["y"])

    def draw(self, cv, lt, lb, dur_b):
        p, E = self.p, self.E
        cv.sphere(165, -10, 90, "dim", spec=False, tone=.8)                       # far side of the gap
        cv.capsule(-140, 150, p["x"] - p["r"] * .6, p["y"] + p["r"] * .6, 9, ramp="body")
        cv.sphere(p["x"], p["y"], p["r"], "body", rim=E(.65))
        cv.ring(p["x"], p["y"], p["r"] - .5, 2, self.A(.55), .9, dashes=1, phase=.15, duty=.45)
        for i, (x, y) in enumerate(self.ves):
            cv.sphere(x + math.sin(lt * 2 + i) * .8, y + math.cos(lt * 1.7 + i) * .8, 5.8, "pale")
        rel = lb - p["release_at"]
        if rel > 0:
            for a, b, c in self.dots:
                k = (rel * .35 + a) % 1.0
                x = p["x"] + p["r"] + 4 + k * 70; y = p["y"] + (b - .5) * 50 * (.3 + k)
                cv.disc(x, y, 1.3, self.pal.ramp("pale", .9))
                if c > .7: cv.glow(x, y, 3, E(.8), .4)


class Junction(Scene):
    """The BUILD: a receiving node with a contracting dashed energy ring and rising glow until `fire_at` (beats)."""
    defaults = {"fire_at": -0.5, "x": 25, "y": -50, "r": 11}

    def setup(self):
        self.tree = []
        for i in range(6):
            a = -math.pi / 2 + (i - 2.5) * .55
            branch_tree(self.rng, self.p["x"] + math.cos(a) * 9, self.p["y"] + math.sin(a) * 9, a, 45, 2.3, 1, self.tree)

    def focus(self, lb, dur_b): return (self.p["x"], self.p["y"])

    def draw(self, cv, lt, lb, dur_b):
        p, E = self.p, self.E
        fire = p["fire_at"] if p["fire_at"] >= 0 else dur_b + p["fire_at"]
        k = min(1.0, max(0.0, lb / max(fire, .1)))
        x, y = p["x"], p["y"]
        cv.polyline([(x, y), (x - 25, y + 50), (x - 70, y + 100), (x - 85, y + 125)], 4.5, ramp="body")
        cv.polyline([(x + 5, y), (x + 60, y + 60), (x + 70, y + 160)], 3.5, ramp="body")
        cv.polyline([(-110, -150), (-60, -60), (-20, -20)], 2.5, ramp="pale")
        cv.sphere(x - 88, y + 135, 18, "body", rim=E(.6))
        for i in range(10):
            u = (lt * .5 + i / 10) % 1.0
            cv.disc(x - 80 + u * 55, y + 120 - u * 70, 1.2, self.pal.ramp("pale", .9))
        draw_tree(cv, self.tree, "body", lit=k, E=E)
        cv.sphere(x, y, p["r"], "body", rim=E(.4 + .5 * k), tone=1 + .3 * k)
        cv.glow(x, y, p["r"] * (1.4 + 1.5 * k), E(.7 + .3 * k), .3 + 1.4 * k ** 2)
        R = p["r"] * (3.2 - 1.8 * ease(k, "inCubic"))
        cv.ring(x, y, R, 1.5, self.A(.4 + .3 * k), .95, dashes=8, phase=lt * .4)

    def sfx(self, dur_b):
        f = self.p["fire_at"] if self.p["fire_at"] >= 0 else dur_b + self.p["fire_at"]
        return [(max(0, f - 2.0), "riser")]


class Network(Scene):
    """A field of many small nodes linked by thin lines; light waves propagate from the centre (system view).
    With flare=true it opens on a white-gold flash + shockwave (the HIT)."""
    defaults = {"nodes": 320, "extent": 440, "flare": False, "wave_every": 4.0, "arcs": 3}

    def setup(self):
        r, n, e = self.rng, self.p["nodes"], self.p["extent"]
        self.nx, self.ny = r.uniform(-e, e, n) * np.array([.8]), r.uniform(-e, e, n)
        self.ns = r.uniform(1.6, 4.0, n); self.na = r.random(n) * TAU
        self.d = np.hypot(self.nx, self.ny)
        idx = np.argsort(self.d)
        self.edges = []
        for i in idx[:n]:
            dd = np.hypot(self.nx - self.nx[i], self.ny - self.ny[i]); dd[i] = 1e9
            for j in np.argsort(dd)[:2]:
                if dd[j] < e * .25: self.edges.append((i, j))
        self.arcs = [(r.uniform(-300, 300), r.uniform(-300, 300), r.uniform(200, 500), r.random() * TAU) for _ in range(self.p["arcs"])]
        self.hub = []
        branch_tree(r, 0, 0, -1.3, 40, 2.2, 2, self.hub); branch_tree(r, 0, 0, 1.0, 50, 2.2, 1, self.hub)
        branch_tree(r, 0, 0, 2.8, 40, 2.2, 2, self.hub)

    def draw(self, cv, lt, lb, dur_b):
        p, E = self.p, self.E
        wr = ((lb % p["wave_every"]) / p["wave_every"]) * p["extent"] * 1.1
        lit = np.exp(-((self.d - wr) / 30) ** 2)
        if p["flare"]: lit = np.maximum(lit, np.exp(-((self.d - lb * 120) / 40) ** 2) * (lb < 4))
        dim = self.pal.ramp("dim", .45)
        for i, j in self.edges:
            cv.line(self.nx[i], self.ny[i], self.nx[j], self.ny[j], .8, dim, .55)
        for cx, cy, R, a0 in self.arcs:
            pts = [(cx + math.cos(a0 + u) * R, cy + math.sin(a0 + u) * R) for u in np.linspace(0, 1.2, 24)]
            cv.polyline(pts, .5, flat=self.pal.ramp("pale", .7), alpha=.7)
            u = (lb * .25) % 1.2; cv.glow(cx + math.cos(a0 + u) * R, cy + math.sin(a0 + u) * R, 4, self.pal.ramp("pale", 1), .9)
        for i in range(len(self.nx)):
            x, y, s = self.nx[i], self.ny[i], self.ns[i]
            for q in range(3):
                a = self.na[i] + q * 2.1
                cv.line(x, y, x + math.cos(a) * s * 3, y + math.sin(a) * s * 3, .7, dim, .8)
            cv.sphere(x, y, s, "body", spec=False, tone=.8 + .4 * lit[i])
            if lit[i] > .15: cv.glow(x, y, s * 3, E(.85), lit[i] * 1.1)
        if p["flare"]:
            f = math.exp(-lb * 1.2)
            draw_tree(cv, self.hub, "pale", lit=f, E=E)
            cv.sphere(0, 0, 8, "body", rim=E(.9))
            zr = 1.0 / max(cv.cam.zoom, 1.0)                     # flare stays ≈ a quarter of the frame at any zoom
            cv.glow(0, 0, (10 + 16 * f) * zr * 1.6, E(1.0), .5 + 1.3 * f)
            cv.glow(0, 0, (4 + 5 * f) * zr * 1.6, self.pal.ramp("pale", 1.0), .6 * f)
            if lb < 2.5:
                cv.ring(0, 0, 10 + ease(lb / 2.5, "outCubic") * 120, 2.5 * (1 - lb / 2.5) + .6, E(.9), 1 - lb / 2.5)

    def sfx(self, dur_b): return [(0, "hit")] if self.p["flare"] else []


class Silhouette(Scene):
    """Particles assemble into a recognisable shape (built-in, glyph:X or a PNG mask) and gold waves sweep it.
    The BIG NUMBER beat ('one of N')."""
    defaults = {"shape": "circle", "size": 150, "x": 0, "y": 15, "n": 1100, "assemble": 2.5, "wave_angle": 25,
                "wavelength": 45, "fill": .35, "glow": .6}

    def setup(self):
        p = self.p
        self.mask = Mask(load_mask(p["shape"], self.base_dir), p["x"], p["y"], p["size"])
        self.tx, self.ty = self.mask.sample(p["n"], self.rng)
        self.sx, self.sy = self.rng.uniform(-260, 260, p["n"]), self.rng.uniform(-400, 400, p["n"])
        self.tw = self.rng.random(p["n"])

    def colours(self, lb, k=1.0):
        a = math.radians(self.p["wave_angle"])
        ph = (self.tx * math.cos(a) + self.ty * math.sin(a)) / self.p["wavelength"] - lb * .5
        w = np.clip((np.sin(ph * TAU) - .4) / .6, 0, 1) * k
        base = self.pal.ramp("pale", .35 + .4 * self.tw)
        return base * (1 - w[:, None]) + self.E(.85)[None] * w[:, None], w

    def draw(self, cv, lt, lb, dur_b):
        p = self.p
        k = ease(lb / p["assemble"], "inOutCubic") if p["assemble"] > 0 else 1.0
        if p["fill"] > 0:
            cv.mask_fill(self.mask.test, self.pal.ramp("dim", .35), alpha=p["fill"] * k)
        x = self.sx + (self.tx - self.sx) * k; y = self.sy + (self.ty - self.sy) * k
        col, w = self.colours(lb, k)
        cv.points(x, y, col, alpha=.95)
        hot = np.nonzero(w > .9)[0][::25]
        for i in hot: cv.glow(x[i], y[i], 5, self.E(.9), p["glow"])


class Object(Scene):
    """The everyday METAPHOR object that contains the system: bulb | battery | jar | can | globe | phone | vinyl | book | image.
    book: see scenes_story.draw_book (hardcover on a desk by a candle; closes at close_at; title + 2-line handle on the cover).
    vinyl: a spinning pixel record (redrawn every frame, never bitmap-rotated) whose groove is a spiral of note heads
    (series values bend the groove), 16 notes per turn so a note passes the needle on every 16th (in sync with a
    rate-4 series voice); upright cream label with the eye mark + legible two-line handle; tonearm with a beat light.
    Inner content = a glowing silhouette; brand text can be etched in-world (brand_at beats)."""
    defaults = {"kind": "bulb", "inner": "circle", "inner_size": 62, "reveal": 2.0, "brand": "", "brand_at": 8.0,
                "level": .8, "image": None, "label": "", "groove": "spiral_notes", "rpm_beats": 4.0, "label_text": "",
                "series": "norgard", "vx": 0.0, "vy": 24.0, "vr": 70.0}

    def setup(self):
        p = self.p
        iy = {"bulb": -30, "jar": -22, "phone": -10}.get(p["kind"], 0)
        self.inner = Silhouette({"shape": p["inner"], "size": p["inner_size"], "y": iy, "n": 650, "assemble": 0,
                                 "wavelength": 25, "fill": .6, "glow": .8}, int(self.rng.integers(1e9)), self.pal, self.base_dir) \
            if p["inner"] and p["kind"] in ("bulb", "jar", "phone") else None
        self.brand = None   # brand is drawn by _brand() (diegetic label)
        self.label = RectMask(text_mask(p["label"]), 0, 0, 10 * (p["label"].count("\n") + 1)) if p["label"] else None
        if p["kind"] == "image":
            from PIL import Image as _I
            import os
            im = _I.open(p["image"] if os.path.isabs(p["image"]) else os.path.join(self.base_dir, p["image"])).convert("RGBA")
            self.img = np.asarray(im, np.float32) / 255

    def focus(self, lb, dur_b):
        if self.p["kind"] == "vinyl": return (self.p["vx"], self.p["vy"])
        if self.p["kind"] == "book": return (0.0, self.p.get("book_y", 6.0))
        return (0.0, -30.0 if self.p["kind"] == "bulb" else 0.0)

    def _outline(self, cv, test, col, alpha):
        wx, wy = cv.world_grid(); e = 1.0 / cv.cam.zoom
        m = test(wx, wy); edge = m & ~(test(wx + e, wy) & test(wx - e, wy) & test(wx, wy + e) & test(wx, wy - e))
        cv._blend((slice(None), slice(None)), edge.astype(np.float32) * alpha, cv._col(col))

    def draw(self, cv, lt, lb, dur_b):
        p, E = self.p, self.E
        a = ease(lb / p["reveal"], "inOutSine") if p["reveal"] > 0 else 1.0
        pale = self.pal.ramp("pale", .85)
        if p["kind"] == "bulb":
            cv.glow(0, -30, 70, E(.6), .35)
            cv.capsule(0, 86, 12, 260, 3, ramp="dim", alpha=a)
            if self.inner: self.inner.draw(cv, lt, lb, dur_b)
            cv.glow(0, -30, 30, E(.8), .5)
            glass = lambda x, y: (np.hypot(x, y + 30) < 56) | ((np.abs(x) < 24 - (y - 15) * .25) & (y > 15) & (y < 55))
            cv.mask_fill(glass, self.pal.ramp("pale", .5), alpha=.08 * a)
            self._outline(cv, glass, pale, .85 * a)
            cv.ring(0, -30, 49, 1.2, self.pal.ramp("pale", 1), .8 * a, dashes=1, phase=-.05, duty=.13)
            cv.line(-6, 50, -3, -5, .8, self.pal.ramp("pale", .6), .8 * a); cv.line(6, 50, 3, -5, .8, self.pal.ramp("pale", .6), .8 * a)
            for i in range(6):
                cv.capsule(-15, 57 + i * 5, 15, 57 + i * 5, 2.6, ramp="energy", alpha=a)
            cv.capsule(-8, 88, 8, 88, 2.5, ramp="dim", alpha=a)
        elif p["kind"] == "battery":
            body = lambda x, y: (np.abs(x) < 36) & (np.abs(y) < 66)
            cv.mask_fill(body, self.pal.ramp("dim", .35), .9 * a)
            self._outline(cv, body, pale, a)
            cv.capsule(-12, -72, 12, -72, 4, ramp="pale", alpha=a)
            n = int(round(p["level"] * 8))
            for i in range(8):
                y = 56 - i * 15
                cv.capsule(-24, y, 24, y, 5, ramp="energy" if i < n else "dim", alpha=a)
                if i < n: cv.glow(0, y, 12, E(.8), .25 * pulse(lb - i * .25, 4, 3))
        elif p["kind"] == "jar":
            body = lambda x, y: ((np.abs(x) < 46) & (np.abs(y) < 60)) | (np.hypot(np.abs(x) - 30, np.abs(y) - 44) < 16)
            body2 = lambda x, y: body(x, y) & ~((np.abs(x) > 30) & (np.abs(y) > 44) & (np.hypot(np.abs(x) - 30, np.abs(y) - 44) > 16))
            cv.glow(0, -20, 60, E(.7), .45 * a)
            if self.inner: self.inner.draw(cv, lt, lb, dur_b)
            cv.mask_fill(body2, self.pal.ramp("energy", .5), .10 * a); self._outline(cv, body2, pale, .9 * a)
            cv.line(-36, -50, -36, 20, 2, self.pal.ramp("pale", 1), .35 * a)
            cv.capsule(-38, -68, 38, -68, 6, ramp="energy", alpha=a)
        elif p["kind"] == "can":
            wx, wy = cv.world_grid()
            body = lambda x, y: (np.abs(x) < 42) & (np.abs(y) < 62)
            m = body(wx, wy)
            shade = np.clip(1 - np.abs(wx + 12) / 60, 0, 1)
            col = self.pal.ramp("body", .25 + .7 * shade)
            cv.rgb[m] = cv.rgb[m] * (1 - a) + col[m] * a
            for yy in (-62, 62): cv.capsule(-42, yy, 42, yy, 3, ramp="pale", alpha=a)
            cv.capsule(-10, -68, 10, -68, 2, ramp="pale", alpha=a)
            cv.line(-30, -50, -30, 50, 2, self.pal.ramp("pale", 1), .5 * a)
        elif p["kind"] == "globe":
            cv.sphere(0, 0, 55, "body", rim=E(.7), alpha=a)
            for k in (-30, 0, 30):
                cv.ring(0, k, math.sqrt(max(1, 55 ** 2 - k * k)), 1, self.pal.ramp("pale", .7), .5 * a, dashes=12, phase=lt * .1)
            cv.ring(0, 0, 70, 1.5, E(.85), .8 * a, dashes=3, phase=lt * .15, duty=.8)
        elif p["kind"] == "phone":
            body = lambda x, y: (np.abs(x) < 42) & (np.abs(y) < 80)
            cv.mask_fill(body, self.pal.ramp("bg", 1), a); self._outline(cv, body, pale, a)
            if self.inner: self.inner.draw(cv, lt, lb, dur_b)
            cv.capsule(-10, -73, 10, -73, 1.5, ramp="pale", alpha=a)
        elif p["kind"] == "vinyl":
            self._vinyl(cv, lt, lb, a)
        elif p["kind"] == "book":
            from .scenes_story import draw_book
            draw_book(self, cv, lt, lb, a)
        elif p["kind"] == "image":
            cv.glow(0, 0, 70, E(.6), .3)
            cv.image(self.img, 0, math.sin(lt * 1.2) * 2, p.get("height", 150), alpha=a)
        if self.label: cv.mask_fill(self.label.test, E(.9), a)
        if p["brand"] and lb >= p["brand_at"] and p["kind"] != "book":     # book: publisher line drawn on the cover
            self._brand(cv, lt, lb, a * ease((lb - p["brand_at"]) / 1.0))

    def _vinyl(self, cv, lt, lb, a):
        from .theory import series_value
        p, E, pal = self.p, self.E, self.pal
        x0, y0, R = p["vx"], p["vy"], p["vr"]; RL = R * .44
        gb = getattr(self, "b0", 0.0) + lb
        th = -TAU * lb / p["rpm_beats"]                                       # clockwise on screen
        cv.glow(x0, y0 + 6, R * 1.15, E(.45), .28 * a)
        cv.glow(x0 - R * .7, y0 - R * .5, R * .6, self.A(.5), .12 * a)
        # disc body: dithered concentric grooves + two fixed specular wedges (light does not rotate with the disc)
        X, Y = cv.to_screen(x0, y0); Rs = cv.sl(R); b = cv._box(X, Y, Rs + 2)
        if b is not None:
            wx, wy = cv.world_grid(); dx, dy = wx[b] - x0, wy[b] - y0
            r = np.hypot(dx, dy); ang = np.arctan2(dy, dx)
            disc = r <= R
            groove = (np.sin(r * TAU / 1.6) > .15) & (r > RL + 3) & (r < R - 2.5)
            col = np.where(groove[..., None], pal.ramp("bg", .38)[None, None], pal.ramp("bg", .05)[None, None])
            spec = np.exp(-((np.angle(np.exp(1j * (ang + 2.3)))) / .32) ** 2) + np.exp(-((np.angle(np.exp(1j * (ang - .84)))) / .32) ** 2)
            spec *= np.clip((r - RL - 2) / 6, 0, 1) * np.clip((R - r) / 3, 0, 1)
            col = col * (1 - .7 * spec[..., None]) + pal.ramp("body", .48)[None, None] * .7 * spec[..., None]
            rim = (r > R - 1.6) & disc
            col[rim] = pal.ramp("body", .3)
            for rr in (RL + 9, RL + 19, RL + 29):                              # track gaps
                gap = np.abs(r - rr) < .8
                col[gap] = pal.ramp("bg", .0)
            m = disc.astype(np.float32) * a
            cv.rgb[b] = cv.rgb[b] * (1 - m[..., None]) + col * m[..., None]
        # spiral groove of note heads: note n sits at the needle angle when the 16th n sounds
        ndl = -.62                                                           # needle angle (screen, rad)
        per_turn = 4 * p["rpm_beats"]; pitch = 3.1
        n_now = gb * 4
        for n in range(int(n_now) - 150, int(n_now) + 40):
            turns = (n - n_now) / per_turn
            r = R - 5 - (n / per_turn - math.floor(gb * 4 / per_turn - 2)) % 10 * pitch
            if r < RL + 4 or r > R - 3: continue
            phi = ndl + TAU * turns
            v = int(series_value(p["series"], abs(n) % 4096)); r2 = r + v * .45
            nx, ny = x0 + r2 * math.cos(phi), y0 + r2 * math.sin(phi)
            since = n_now - n
            lit = math.exp(-since * .35) if since >= 0 else 0.0
            sp = max(math.exp(-((math.atan2(math.sin(phi + 2.3), math.cos(phi + 2.3))) / .35) ** 2),
                     math.exp(-((math.atan2(math.sin(phi - .84), math.cos(phi - .84))) / .35) ** 2))
            c = pal.ramp("body", .55 + .3 * sp) * (1 - lit) + E(.95) * lit
            cv.ellipse(nx, ny, 1.5, 1.05, c, a, ang=phi + math.pi / 2)
            if lit > .5: cv.glow(nx, ny, 3, E(.9), .5 * lit * a)
        # label (upright: text never rotates), rotating rim ticks show the spin
        cv.disc(x0, y0, RL + 1.2, pal.ramp("accent", .45), a)
        cv.disc(x0, y0, RL, pal.ramp("pale", 1.0), a)
        # matte paper: glow accumulated so far (disc glow, rays) is additive at composite time and dithered the thin
        # small-print strokes into cream; the label does not glow, so clear the light buffer under it
        LX, LY = cv.to_screen(x0, y0); lb_ = cv._box(LX, LY, cv.sl(RL + 1.2))
        if lb_ is not None:
            under = np.hypot(cv.xs[lb_] - LX, cv.ys[lb_] - LY) <= cv.sl(RL + 1.2)
            cv.glowbuf[lb_][under] *= 1 - .9 * a
        cv.ring(x0, y0, RL - 2.2, .8, pal.ramp("accent", .5), .9 * a, dashes=24, phase=-lb / p["rpm_beats"], duty=.5)
        # (no spindle dot on the label: it sat right after the handle's last glyph and turned ".piksel" into ".pikse]")
        # tonearm (swings in over the first beat), headshell with a beat light at the needle
        sw = ease(min(1, max(0, lb) / 1.0), "outCubic")
        px_, py_ = x0 + R * .95, y0 - R * .98
        nr = R - 5 - ((n_now / per_turn) - math.floor(gb * 4 / per_turn - 2)) % 10 * pitch
        tx, ty = x0 + nr * math.cos(ndl), y0 + nr * math.sin(ndl)
        tx, ty = px_ + (tx - px_) * (.55 + .45 * sw), py_ + (ty - py_) * (.55 + .45 * sw) - (1 - sw) * 25
        cv.disc(px_, py_, 7, pal.ramp("pale", .45), a); cv.disc(px_, py_, 4.5, pal.ramp("pale", .8), a)
        cv.capsule(px_, py_, tx + 4, ty - 6, 1.6, ramp="pale", alpha=a)
        cv.capsule(tx + 4, ty - 6, tx, ty, 1.3, ramp="pale", alpha=a)
        cv.rect(tx + 1, ty - 1, 5, 4, pal.ramp("pale", .6), a)
        bl = pulse(gb, 1.0, 5.0)
        cv.glow(tx, ty, 4 + 4 * bl, E(.9), (.5 + .6 * bl) * a); cv.disc(tx, ty, 1.1, E(1.0), a)

    def _brand(self, cv, lt, lb, a):
        """Kind-specific diegetic label (the phone-legible placement of the channel tag)."""
        from .bitmap import draw_text, draw_mark
        from .props import _rect, _frame, terminal, plate
        pal, h, k = self.pal, self.p["brand"], self.p["kind"]
        two = h.replace(".", "\n.", 1) if "." in h else h
        if k == "bulb":
            draw_mark(cv, pal, 0, -66, .8, alpha=.8 * a, glow=0, mono=pal.ramp("pale", .95))
            draw_text(cv, h, 0, -54, 1, pal.ramp("pale", .95), alpha=.9 * a)
        elif k in ("jar", "can", "battery"):
            y = {"jar": 34, "can": 8, "battery": 4}[k]; w = {"jar": 88, "can": 84, "battery": 74}[k]
            band = pal.ramp("pale", 1.0) if k != "battery" else pal.ramp("accent", .45)
            _rect(cv, 0, y, w, 46, band, a); _frame(cv, 0, y, w - 4, 42, pal.ramp("accent", .5) if k != "battery" else pal.ramp("pale", 1), 1.2, a)
            draw_mark(cv, pal, -w / 2 + 14, y, 1.0, alpha=a, glow=0, outline=pal.ramp("bg", .3) if k != "battery" else None)
            draw_text(cv, two, 8, y, 1, pal.ramp("bg", .3) if k != "battery" else pal.ramp("pale", 1), alpha=a)
        elif k == "phone":
            terminal_lines = [h, "> merak: %100", "> HAYRET!"]
            for i, l in enumerate(terminal_lines):
                n = int(max(0, lb - self.p["brand_at"]) * 7) - sum(len(x) + 3 for x in terminal_lines[:i])
                if n > 0: draw_text(cv, l[:n], 0, 40 + i * 12, 1, pal.ramp("energy" if i < 2 else "accent", .75), alpha=a)
        elif k == "vinyl":
            from .minifont import draw_mini
            x, y = self.p["vx"], self.p["vy"]; ink = pal.ramp("bg", .3)
            # snap=True: pixel-exact stamps (k×k art px per dot) so the handle never drops/doubles a column mid-zoom
            draw_mark(cv, pal, x, y - 18, 1.0, alpha=a, glow=0, outline=ink, snap=True)
            draw_text(cv, two, x, y - 1, 1, ink, alpha=a, snap=True)
            if self.p["label_text"]:
                lt_ = self.p["label_text"].replace("\n", " ")
                cv.rect(x, y + 16, len(lt_) * 4 + 3, 8, pal.ramp("pale", 1.0), a)          # clean paper strip under the small print
                draw_mini(cv, lt_, x, y + 16, 1.0, pal.ramp("accent", .45), alpha=a, snap=True)
        elif k == "globe":
            from .props import patch
            patch(cv, pal, lt, lb, 0, 92, .8, h)
        else:
            plate(cv, pal, lt, lb, 0, 95, .9, h)

    def sfx(self, dur_b):
        out = [(0, "shimmer")]
        if self.p["kind"] == "book" and self.p.get("state", "closing") == "closing":
            out.append((self.p.get("close_at", .5), "thud"))                # the cover slams shut
        return out


class ImageScene(Scene):
    """Any user PNG (drawn at native source resolution, quantised to the palette) with glow + float."""
    defaults = {"image": None, "height": 160, "glow": .5, "float": 2.0}

    def setup(self):
        import os
        path = self.p["image"]; path = path if os.path.isabs(path) else os.path.join(self.base_dir, path)
        self.img = np.asarray(Image.open(path).convert("RGBA"), np.float32) / 255

    def draw(self, cv, lt, lb, dur_b):
        cv.glow(0, 0, self.p["height"] * .45, self.E(.6), self.p["glow"])
        cv.image(self.img, 0, math.sin(lt * 1.1) * self.p["float"], self.p["height"])


class Void(Scene):
    """Only the ambient world (gradient + dust); for title cards or breathing room."""
    def draw(self, cv, lt, lb, dur_b): pass


SCENES = {"hero": Hero, "lattice": Lattice, "chain": Chain, "streaks": Streaks, "pod": Pod, "junction": Junction,
          "network": Network, "silhouette": Silhouette, "object": Object, "image": ImageScene, "void": Void}

from . import scenes_music, scenes_math, scenes_story, scenes_vision, scenes_cosmos, scenes_chalk, scenes_sync   # noqa: E402,F401  (they register fractal_staff, noise_scope, series_tree,
                                          #  shepard_stairs, koch, mandel_zoom into SCENES themselves)
