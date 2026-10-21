"""Cosmos scenes (evren-anlamak): powers-of-ten cosmic zoom and a galaxy chessboard that becomes a board of boards.

cosmic_zoom   One nested universe drawn as five tableaux, each at its own scale: kid (a child with a telescope on a
              night hill) → earth → solar (system) → galaxy → web (cosmic web). Stage j is drawn at 10^(j−Z) art px per
              stage unit; Z (log10 zoom) is the SCENE's zoom, so the film camera stays 1.0. Stages are rigidly nested
              (ANCHOR[j] = where stage j−1 sits inside stage j); a stage dither-dissolves away when it shrinks below
              `fade` (1/8 → 1/16 of the frame) and its proxy in the next stage (earth dot, sun star, galaxy speck) takes
              over. A slow dark-matter haze (palette 'dim' ramp, ~60 % of the screen, never resolves into shapes) sits
              behind everything. All motion runs on the GLOBAL beat with an integer number of cycles per film, so S10
              (`rewind_to_frame0`) lands exactly on frame 0 of S1. rewind_turn [t0, t1] (beats): the rewind starts on
              the close-up "front" pose, turns via "q" at t0 and is back to "up" at t1 (no pose pop after S9).
              const_y [y, y, y]: centre y (world) of each sky equation (default -96 / -50 / -4).
  params      from/to (stage names; Z interpolates with `ease`), stages (["sky"] = the kid's sky, constellations
              "equations" draw E=mc², F=ma and the field equation between stars over `draw_beats`), kid_turns (close-up:
              the kid turns to the camera over `turn_beats` from `turn_at`; at `eye_glint_at` the hayret eye glints
              for 1 beat), rewind_to_frame0 (Z from the deepest stage back to 0, `rewind_ease`), kid_view (view centre
              relative to the kid at Z=0 → kid at 0.62–0.78 H), haze (0..1).
galaxy_chess  An 8×8 board in space whose pieces are tiny galaxies. `ca_rule` lights one row per generation of an
              elementary CA; with `ca_series` (default: the music series that plays it) every lit cell appears on the
              16th where its note sounds — read from spec.music.series_defs and the same section/phase rule as
              music.series_notes, so picture and melody cannot drift. `move_every`: a piece slides one move.
              `zoom_out_boards`: each square is itself a board (powers of 8, per-pixel LOD), the scene zooms out until
              the Rule-30 triangle of a 512-cell CA appears across the board of boards; `counter` rolls 10¹ → 10ⁿ."""
import math
import numpy as np
from .scenes import Scene, SCENES, ease
from .raster import Camera
from .palette import BAYER4
from .scenes_vision import vnoise, _h
from .sprites_kid import draw_kid, KID
from .bitmap import Bitmap, draw_bitmap, draw_text, draw_mark, text_bitmap
from .pixfont import SUPERSCRIPT

TAU = math.pi * 2


def _hex(h):
    h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def smooth(x, a, b):
    t = min(max((x - a) / (b - a), 0.0), 1.0) if b != a else float(x >= a)
    return t * t * (3 - 2 * t)


def _bayer(H, W):
    return np.tile(BAYER4, (H // 4 + 1, W // 4 + 1))[:H, :W]


def dither_draw(cv, alpha, fn):
    """Ordered-dither crossfade of a draw call: pixels it paints survive only where Bayer < alpha (screen-anchored),
    its additive light is scaled by alpha."""
    if alpha <= 0.0: return
    if alpha >= 1.0: return fn()
    before, gb = cv.rgb.copy(), cv.glowbuf.copy()
    fn()
    keep = _bayer(cv.H, cv.W) < alpha
    cv.rgb[~keep] = before[~keep]
    cv.glowbuf[:] = gb + (cv.glowbuf - gb) * alpha


class _Loop:
    """global-beat clock helpers: phases with an integer number of cycles per film (loop-exact)"""
    def B(self, lb): return self.gbeat(lb)

    def ph(self, B, period, off=0.0):
        T = self.total or 80.0; n = max(1, int(round(T / max(period, 1e-6))))
        return TAU * B * n / T + off


# ================================================================================================ cosmic zoom
STAGES = ["kid", "earth", "solar", "galaxy", "web"]
ANCHOR = {1: (0.0, -41.4), 2: (-26.0, -7.5), 3: (36.0, 16.0)}        # stage j−1's origin inside stage j; 4 → web filament
EXTENT = {0: 130.0, 1: 92.0, 2: 175.0, 3: 175.0}                       # stage size (its own units) for the fade rule
EARTH_R, HILL_R = 40.0, 414.0
SUN_DIR = np.array([.93, .27, .25], np.float32) / np.linalg.norm([.93, .27, .25])
PLANETS = [  # (orbit rx, radius, colour, cycles per film, phase)
    (13.0, .9, "#BFD6DC", 3, .5), (20.0, 1.5, "#FFF1C8", 2, 2.2), (40.0, 1.3, "#FF9A86", 1, 4.0),
    (60.0, 3.4, "#FFC860", 1, 1.25), (80.0, 2.9, "#FFF1C8", 1, 5.3)]

# stroke glyphs for star constellations: polylines on a 4×6 cell (y down; μ descends to 7); "²" is drawn raised & small
STROKE = {
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]], "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    "=": [[(0, 2), (4, 2)], [(0, 4), (4, 4)]], "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "m": [[(0, 6), (0, 2.5), (1, 2), (2, 2.6), (2, 6)], [(2, 2.6), (3, 2), (4, 2.5), (4, 6)]],
    "c": [[(4, 2.6), (3, 2), (1, 2), (0, 3), (0, 5), (1, 6), (3, 6), (4, 5.4)]],
    "a": [[(.5, 2.4), (3, 2), (4, 3), (4, 6)], [(4, 4), (1, 4), (0, 5), (1, 6), (4, 5.5)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.5), (2.4, 3.5)]],
    "8": [[(2, 3), (.6, 2.2), (.6, .8), (2, 0), (3.4, .8), (3.4, 2.2), (2, 3), (0, 4), (0, 5.2), (2, 6), (4, 5.2), (4, 4), (2, 3)]],
    "π": [[(0, 2.5), (4, 2.5)], [(1, 2.5), (1, 6)], [(3, 2.5), (3, 6)]],
    "μ": [[(0, 7.5), (0, 2)], [(0, 5), (1, 6), (3, 6), (4, 5)], [(4, 2), (4, 6)]], "ν": [[(0, 2), (2, 6), (4, 2)]],
    "2": [[(0, .8), (1, 0), (3, 0), (4, .9), (0, 6), (4, 6)]],
}
EQUATIONS = [  # (tokens [(char, scale, dy)], centre y (world), glyph height)
    ([("E", 1, 0), ("=", 1, 0), ("m", 1, 0), ("c", 1, 0), ("2", .5, -1.2)], -96.0, 17.0),
    ([("F", 1, 0), ("=", 1, 0), ("m", 1, 0), ("a", 1, 0)], -50.0, 17.0),
    ([("G", 1, 0), ("μ", .5, 5.2), ("ν", .5, 5.2), ("=", 1, 0), ("8", 1, 0), ("π", 1, 0), ("T", 1, 0), ("μ", .5, 5.2),
      ("ν", .5, 5.2)], -4.0, 14.0),
]


class CosmicZoom(Scene, _Loop):
    own_layers = 3          # dark-matter haze (drifts), twinkling starfield, the stage tableau (ridges / grass / fireflies)
    defaults = {"from": "kid", "to": "web", "stages": STAGES, "ease": "inOutSine", "constellations": None,
                "draw_beats": 4.0, "draw_at": 0.5, "kid_turns": False, "eye_glint_at": 6.0, "turn_at": 1.0,
                "turn_beats": 2.0, "rewind_to_frame0": False, "rewind_ease": "inOutCubic", "haze": 0.6,
                "kid_view": [0.0, -88.0], "close_z": -0.36, "close_view": [0.0, -19.5], "sky_view": [38.0, -150.0],
                "fade": [1 / 8, 1 / 16], "kid_scale": 2.0, "stars": 320, "world_seed": 2026, "rewind_turn": None, "const_y": None}

    def setup(self):
        p = self.p; rng = np.random.default_rng(int(p["world_seed"]))      # ONE world for every segment that uses it
        n = int(p["stars"])
        self.st_u, self.st_v = rng.random(n), rng.random(n)
        r = rng.random(n); self.st_mag = np.where(r < .06, 2, np.where(r < .3, 1, 0))
        pick = rng.random(n)
        self.st_col = np.stack([_hex("#FFF1C8") if q < .12 else _hex("#FF9AD0") if q < .2 else _hex("#5FD6F0") if q < .3
                                else _hex("#EEF6F6") if q < .55 else _hex("#BFD6DC") for q in pick])
        self.st_ph = rng.random(n) * TAU; self.st_per = rng.uniform(2.2, 7.0, n)
        self._galaxy(rng); self._web(rng)
        self.towns = [(x, rng.random()) for x in np.r_[np.arange(-140, -46, 5.5), np.arange(46, 140, 6.5)] if rng.random() < .55]
        self.flies = [(rng.uniform(-70, 70), rng.uniform(-14, 6), rng.random() * TAU, rng.uniform(4, 11)) for _ in range(6)]
        self.grass = np.arange(-150, 150, 2.2) + rng.uniform(-.6, .6, len(np.arange(-150, 150, 2.2)))
        self.grass_h = rng.uniform(1.6, 4.2, len(self.grass))
        self.mw = None

    # ------------------------------------------------------------------ world construction
    def _galaxy(self, rng):
        pts, cols, al = [], [], []
        for arm in range(5):
            main = arm < 2; m = 2300 if main else (500 if arm < 4 else 900)
            u = rng.random(m) ** .8; rr = 6 + 72 * u
            th = (arm * math.pi if main else arm * math.pi / 2 + .7) + np.log(rr / 6) / math.tan(math.radians(15))
            sig = .13 if main else (.22 if arm < 4 else 1.6)
            th += rng.normal(0, sig, m); rr = rr + rng.normal(0, 1.2 + rr * .035, m)
            x, y = rr * np.cos(th), rr * np.sin(th)
            pts.append(np.stack([x, y], 1))
            c = rng.random(m)
            cols.append(np.where(c[:, None] < .08, _hex("#FF9AD0"), np.where(c[:, None] < .4, _hex("#C99AE0"),
                        np.where(c[:, None] < .62, _hex("#9C66C8"), np.where(c[:, None] < .72, _hex("#5FD6F0"), _hex("#F3E6FA"))))))
            al.append(np.clip((1.0 if main else .55) - u * .45 + rng.normal(0, .1, m), .2, 1))
        core = rng.normal(0, 6.5, (900, 2)); pts.append(core)
        cols.append(np.where(rng.random(900)[:, None] < .5, _hex("#FFC860"), _hex("#FFF1C8"))); al.append(np.full(900, .9))
        P = np.concatenate(pts); ca, sa = math.cos(.5), math.sin(.5)
        x, y = P[:, 0] * ca - P[:, 1] * sa, (P[:, 0] * sa + P[:, 1] * ca) * .64                    # tilt + spin
        self.g_xy = np.stack([x, y], 1).astype(np.float32); self.g_col = np.concatenate(cols).astype(np.float32)
        self.g_a = np.concatenate(al).astype(np.float32)
        far = np.hypot(x - ANCHOR[3][0], y - ANCHOR[3][1]) > 3.0           # keep the sun's own spot clear
        self.g_xy, self.g_col, self.g_a = self.g_xy[far], self.g_col[far], self.g_a[far]
        k = rng.random(len(self.g_xy)) < .12                                  # dust lanes: dark specks on the inner arms
        rr = np.hypot(self.g_xy[:, 0], self.g_xy[:, 1] / .64)
        self.g_dust = k & (rr > 10) & (rr < 50)

    def _web(self, rng):
        gx, gy = np.meshgrid(np.arange(-5, 6), np.arange(-7, 8))
        nodes = np.stack([gx.ravel() * 46.0, gy.ravel() * 52.0], 1) + rng.normal(0, 15, (gx.size, 2))
        edges = set()
        for i, q in enumerate(nodes):
            d = np.hypot(*(nodes - q).T); d[i] = 1e9
            for j in np.argsort(d)[:3]:
                if d[j] < 95: edges.add((min(i, j), max(i, j)))
        pts, br = [], []
        best = (1e9, None)
        for i, j in edges:
            a, b = nodes[i], nodes[j]; L = float(np.hypot(*(b - a))); m = int(L / 1.1)
            t = rng.random(m); pp = a + (b - a) * t[:, None] + rng.normal(0, 1, (m, 2)) * (1.0 + 2.2 * (1 - np.abs(2 * t - 1)) ** 2)[:, None]
            pts.append(pp); br.append(np.clip(.35 + .5 * np.abs(2 * t - 1) ** 2 + rng.normal(0, .12, m), .15, 1))
            # our galaxy: a point on the filament nearest the web centre
            tt = np.clip(-np.dot(a, b - a) / max(L * L, 1e-9), .2, .8); q = a + (b - a) * tt
            if np.hypot(*q) < best[0]: best = (float(np.hypot(*q)), q)
        self.w_xy = np.concatenate(pts).astype(np.float32); self.w_b = np.concatenate(br).astype(np.float32)
        self.w_nodes = nodes; self.w_deg = np.bincount(np.array(list(edges)).ravel(), minlength=len(nodes))
        self.anchor4 = (float(best[1][0]), float(best[1][1]))
        keep = np.hypot(self.w_xy[:, 0] - self.anchor4[0], self.w_xy[:, 1] - self.anchor4[1]) > 1.2
        self.w_xy, self.w_b = self.w_xy[keep], self.w_b[keep]

    def anchor(self, j):
        return self.anchor4 if j == 4 else ANCHOR[j]

    # ------------------------------------------------------------------ zoom state
    def Z(self, lb, dur_b):
        p = self.p
        if p["stages"] == ["sky"] or p.get("constellations"): return 0.0
        if p["kid_turns"]: return float(p["close_z"])
        if p["rewind_to_frame0"]:
            e = ease(min(max(lb / max(dur_b, 1e-6), 0.0), 1.0), p["rewind_ease"])
            if p.get("rewind_from", "close") == "close":      # pull back from the S9 close-up to the frame-0 shot
                cv_, kv = np.array(p["close_view"], float), np.array(p["kid_view"], float)
                self._view = tuple(cv_ + (kv - cv_) * e)
                return float(p["close_z"]) * (1 - e)
            z0 = float(STAGES.index(p["rewind_from"]))
            return z0 * (1 - e)
        a, b = STAGES.index(p["from"]), STAGES.index(p["to"])
        return a + (b - a) * ease(lb / max(dur_b, 1e-6), p["ease"])

    def view0(self):
        p = self.p
        if p["rewind_to_frame0"] and getattr(self, "_view", None) is not None: return self._view
        if p["stages"] == ["sky"] or p.get("constellations"): return tuple(p["sky_view"])
        if p["kid_turns"]: return tuple(p["close_view"])
        return tuple(p["kid_view"])

    def chain(self, Z):
        """→ {stage j: view centre Q_j in stage-j units} (rigid nesting: Q_{j−1} = 10 (Q_j − A_j))"""
        n = 4; i = int(min(max(math.floor(Z), 0), n - 1)); e = smooth(Z - i, 0.0, 1.0)
        v0 = np.array(self.view0(), np.float64)
        start = np.array(self.anchor(i + 1), np.float64) + (v0 / 10.0 if i == 0 else 0.0)
        Q = {i + 1: start * (1 - e)}
        for j in range(i + 1, 0, -1): Q[j - 1] = (Q[j] - np.array(self.anchor(j))) * 10.0
        for j in range(i + 2, n + 1): Q[j] = np.array(self.anchor(j)) + Q[j - 1] / 10.0
        return Q

    def stage_alpha(self, j, Z, zc=1.0):
        if j >= 4: return 1.0
        a, b = self.p["fade"]; ext = EXTENT[j] * 10 ** (j - Z) * zc / 180.0
        return smooth(ext, b, a)

    def _cam(self, cv, base, Q, j, Z):
        s = 10 ** (j - Z)
        cv.set_cam(Camera(float(Q[j][0]) + base.cx / s, float(Q[j][1]) + base.cy / s, base.zoom * s, base.rot))
        return s

    def focus(self, lb, dur_b):
        Z = self.Z(lb, dur_b); Q = self.chain(Z)
        return tuple((-Q[0] * 10 ** (-Z)).tolist())          # the kid, in film world units

    # ------------------------------------------------------------------ draw
    def draw(self, cv, lt, lb, dur_b):
        p = self.p; base = cv.cam; B = self.B(lb); Z = self.Z(lb, dur_b); Q = self.chain(Z)
        sky = p["stages"] == ["sky"] or bool(p.get("constellations"))
        self._space(cv, B, Z)
        cv.set_cam(Camera(0, 0, 1, 0)); self._haze(cv, B)
        if sky: self._milkyway(cv, B)
        self._stars(cv, B, 1.0 - smooth(Z, 1.7, 2.6), dense=sky)
        cv.set_cam(base)
        if sky:
            self._constellations(cv, B, lb)
            self._cam(cv, base, Q, 0, 0.0); self._kid_stage(cv, B, lb, 1.0, frame="up", close=False)
            cv.set_cam(base); return
        a = {j: self.stage_alpha(j, Z, base.zoom) for j in range(5)}
        if Z > 2.5:
            s = self._cam(cv, base, Q, 4, Z); dither_draw(cv, smooth(Z, 2.55, 3.3), lambda: self._web_draw(cv, B, s, 1 - a[3]))
        if Z > 1.22:
            s = self._cam(cv, base, Q, 3, Z); ga = smooth(Z, 1.25, 1.9)
            dither_draw(cv, a[3] * ga if Z > 3 else ga, lambda: self._galaxy_draw(cv, B, s, 1 - a[2]))
        if a[2] > 0 and Z > .22:
            s = self._cam(cv, base, Q, 2, Z); dither_draw(cv, a[2], lambda: self._solar(cv, B, s, 1 - a[1]))
        if a[1] > 0 and Z < 2.2:
            s = self._cam(cv, base, Q, 1, Z); dither_draw(cv, a[1], lambda: self._earth(cv, B, s))
        if a[0] > 0:
            self._cam(cv, base, Q, 0, Z)
            dither_draw(cv, a[0], lambda: self._kid_stage(cv, B, lb, smooth(-Z, -.5, 0.0) if Z > 0 else 1.0,
                                                          frame=self._kid_frame(B, lb), close=p["kid_turns"] or bool(p.get("rewind_turn"))))
        cv.set_cam(base)

    # ---- screen-space backdrop
    def _space(self, cv, B, Z):
        top, bot = cv.pal.ramp("bg", .05), cv.pal.ramp("bg", .45)
        # ground-level sky (atmosphere): violet glow toward the horizon, gone once we leave the planet
        atm = 1.0 - smooth(Z, .08, .6)
        t = (cv.ys / cv.H)[..., None]
        col = top * (1 - t) + bot * t
        if atm > 0:
            g = np.clip((cv.ys / cv.H - .25) / .5, 0, 1)[..., None] ** 1.6
            col = col * (1 - g * atm * .7) + cv.pal.ramp("body", .22) * g * atm * .7
        cv.rgb[:] = col

    def _haze(self, cv, B):
        k = float(self.p["haze"])
        if k <= 0: return
        dx, dy = 3.0 * math.sin(self.ph(B, 80)), 2.0 * math.cos(self.ph(B, 80))
        X, Y = cv.xs / 46.0 + dx, cv.ys / 46.0 + dy
        n = vnoise(X, Y, 3.1) * .62 + vnoise(X * 2.1 + 4, Y * 2.1 - 2, 5.7) * .38
        w = np.clip((n - .38) / .34, 0, 1) ** 1.3 * k                       # ≈ 60 % of the area > 0
        col = cv.pal.ramp("dim", np.clip(.45 + .55 * n, 0, 1))
        cv.rgb[:] = cv.rgb * (1 - w[..., None] * .55) + col * (w[..., None] * .55)

    def _stars(self, cv, B, alpha, dense=False):
        if alpha <= 0: return
        n = len(self.st_u) if dense else int(len(self.st_u) * .72)
        X, Y = self.st_u[:n] * cv.W - cv.W / 2, self.st_v[:n] * cv.H - cv.H / 2
        tw = .62 + .38 * np.sin(self.st_ph[:n] + np.array([self.ph(B, q) for q in self.st_per[:n]]))
        base = np.where(self.st_mag[:n] == 2, 1.0, np.where(self.st_mag[:n] == 1, .78, .5))
        a = np.clip(base * tw * alpha, 0, 1)
        cv.points(X, Y, self.st_col[:n], a)
        big = np.nonzero(self.st_mag[:n] == 2)[0]
        for i in big:
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cv.points(np.array([X[i] + ox]), np.array([Y[i] + oy]), self.st_col[i], a[i] * .45 * (tw[i] > .8))

    def _milkyway(self, cv, B):
        if self.mw is None:
            rng = np.random.default_rng(77); m = 1400; t = rng.random(m)
            x = -110 + 220 * t; y = 120 - 330 * t + rng.normal(0, 18 + 10 * np.sin(t * 7), m)
            self.mw = (x, y, rng.random(m))
        x, y, r = self.mw
        cv.points(x, y, np.where(r[:, None] < .2, _hex("#C99AE0"), _hex("#9C66C8")), .25 + .35 * r)
        for k in range(7):
            t = k / 6; cv.glow(-100 + 200 * t, 110 - 300 * t, 34, cv.pal.ramp("body", .35), .16)

    # ---- stage 4: cosmic web
    def _web_draw(self, cv, B, s, proxy_a):
        b = self.w_b; col = cv.pal.ramp("body", np.clip(.45 + .55 * b, 0, 1)) * 1.0
        hot = b > .75; col[hot] = cv.pal.ramp("accent", .75)
        cv.points(self.w_xy[:, 0], self.w_xy[:, 1], col, np.clip(.45 + .55 * b, 0, 1))
        for (x, y), d in zip(self.w_nodes, self.w_deg):
            if d >= 3 and s < 3:
                cv.glow(float(x), float(y), 3.2 + .8 * d, cv.pal.ramp("accent", .55), .32)
                cv.disc(float(x), float(y), .9 + .25 * d, cv.pal.ramp("pale", .95), .9)
        if proxy_a > 0:
            ax, ay = self.anchor4
            dither_draw(cv, proxy_a, lambda: (cv.glow(ax, ay, 1.2, cv.pal.ramp("energy", .8), .9),
                                              cv.disc(ax, ay, .5, cv.pal.ramp("energy", 1.0), 1.0)))
            if s * cv.cam.zoom / max(s, 1e-9) and s < 1.6:                  # "you are here": a slow pale ring
                X, Y = cv.to_screen(ax, ay); r = 6 + 2 * math.sin(self.ph(B, 4))
                cv.ring(ax, ay, r / cv.cam.zoom, 1.0 / cv.cam.zoom, cv.pal.ramp("pale", .7), .55 * proxy_a)

    # ---- stage 3: spiral galaxy
    def _galaxy_draw(self, cv, B, s, proxy_a):
        xy = self.g_xy; tw = .8 + .2 * np.sin(np.arange(len(xy)) * 1.7 + self.ph(B, 5))
        cv.points(xy[~self.g_dust, 0], xy[~self.g_dust, 1], self.g_col[~self.g_dust], np.clip(self.g_a[~self.g_dust] * tw[~self.g_dust], 0, 1))
        cv.points(xy[self.g_dust, 0], xy[self.g_dust, 1], cv.pal.ramp("bg", .1), .7)
        if s < 6:
            cv.glow(0, 0, 13, cv.pal.ramp("energy", .75), .55); cv.glow(0, 0, 30, cv.pal.ramp("body", .5), .22)
            for k in range(10):
                a = k * 1.3 + .5; r = 18 + 5 * k
                cv.glow(r * math.cos(a) * .9, r * math.sin(a) * .58, 5, cv.pal.ramp("accent", .6), .12)
        if proxy_a > 0:
            sx, sy = ANCHOR[3]
            dither_draw(cv, proxy_a, lambda: (cv.glow(sx, sy, .9, cv.pal.ramp("energy", .9), .8),
                                              cv.points(np.array([sx]), np.array([sy]), cv.pal.ramp("energy", 1.0), 1.0)))

    # ---- stage 2: solar system
    def _solar(self, cv, B, s, proxy_a):
        pal = cv.pal; zs = cv.cam.zoom
        for rx, *_ in PLANETS + [(30.0,)]:
            n = int(np.clip(TAU * rx * zs / 3.5, 24, 1600)); t = np.linspace(0, TAU, n, endpoint=False)
            cv.points(rx * np.cos(t), rx * .5 * np.sin(t), pal.ramp("dim", .9), .55)
        rng = np.random.default_rng(5); m = 260; t = rng.random(m) * TAU + self.ph(B, 80); r = rng.uniform(46, 53, m)
        cv.points(r * np.cos(t), r * .5 * np.sin(t), pal.ramp("pale", .35), .5)
        cv.glow(0, 0, 16, pal.ramp("energy", .7), .6); cv.glow(0, 0, 6, pal.ramp("energy", 1.0), .6)
        cv.sphere(0, 0, 6.2, ramp="energy", light=(-.2, -.3), spec=False, tone=1.15)
        for rx, r, c, cyc, ph0 in PLANETS:
            a = self.ph(B, (self.total or 80) / cyc, ph0) if cyc else ph0
            x, y = rx * math.cos(a), rx * .5 * math.sin(a)
            col = _hex(c)
            cv.disc(x, y, r, col * .55, 1.0)
            cv.disc(x - r * .25, y - r * .2, r * .78, col, 1.0)
            if rx == 60.0:
                for k in (-1, 1): cv.line(x - r * .8, y + k * r * .35, x + r * .8, y + k * r * .35, .5, _hex("#B8782A"), .9)
            if rx == 80.0: cv.ellipse(x, y, r * 2.1, r * .55, _hex("#BFD6DC"), .55, ang=-.25)
        if proxy_a > 0:
            ex, ey = ANCHOR[2]
            def proxy():
                cv.disc(ex, ey, EARTH_R / 10, _hex("#1F1752"), 1.0)
                cv.disc(ex + .9, ey + .2, EARTH_R / 10 * .82, _hex("#2A8FB8"), 1.0)
                cv.disc(ex + 6.4 * .8, ey - 6.4 * .6, .6, _hex("#BFD6DC"), 1.0)
            dither_draw(cv, proxy_a, proxy)

    # ---- stage 1: earth (per-pixel sphere, periodic texture → loop-exact rotation)
    def _earth(self, cv, B, s):
        pal = cv.pal; X, Y = cv.to_screen(0.0, 0.0); Rs = cv.sl(EARTH_R)
        if Rs < .8: return
        mx, my = 64.0, -60.0                                                   # moon
        cv.sphere(mx, my, 6.0, ramp="pale", light=(.85, .2), spec=False, tone=.95)
        for cx, cy, cr in ((-1.5, -1.0, 1.2), (1.8, 1.6, .9), (-.5, 2.4, .6)):
            cv.disc(mx + cx, my + cy, cr, pal.ramp("pale", .35), .6)
        b = cv._box(float(X), float(Y), Rs * 1.12 + 2)
        if b is None: return
        nx, ny = (cv.xs[b] - X) / Rs, (cv.ys[b] - Y) / Rs; d = np.sqrt(nx * nx + ny * ny)
        inside = d <= 1.0; nz = np.sqrt(np.clip(1 - d * d, 0, 1))
        lam = nx * SUN_DIR[0] + ny * SUN_DIR[1] + nz * SUN_DIR[2]
        lon = np.arctan2(nx, nz + 1e-6) + self.ph(B, self.total or 80); lat = np.arcsin(np.clip(ny, -1, 1))
        cl, sl = np.cos(lon), np.sin(lon)
        def fbm(k, sd):
            return (vnoise(cl * k + 7, sl * k + lat * k * .8, sd) * .5 + vnoise(cl * k * 2.1 - 3, sl * k * 2.1 + lat * k * 1.7, sd + 1) * .3
                    + vnoise(cl * k * 4.3 + 1, sl * k * 4.3 + lat * k * 3.4, sd + 2) * .2)
        hgt = fbm(2.6, 3.3); land = hgt > .55; ice = np.abs(lat) > 1.25
        cloud = (fbm(3.6, 13.7) > .6) & (Rs > 6)
        day = np.clip(lam * 1.25, 0, 1)[..., None]
        night = pal.ramp("bg", .62)
        ocean_d = night * (1 - day) + (_hex("#1F1752") * .35 + _hex("#2A8FB8") * .65) * day
        lc = np.where((hgt > .66)[..., None], _hex("#B8782A") * .5 + _hex("#7FA3B0") * .5, _hex("#4E6A78") * .6 + _hex("#7FA3B0") * .4)
        land_d = (night * .8 + pal.ramp("dim", .45) * .2) * (1 - day) + lc * day
        col = np.where(land[..., None], land_d, ocean_d)
        col = np.where(ice[..., None], night * (1 - day) + _hex("#EEF6F6") * day, col)
        col = np.where(cloud[..., None], col * (1 - .7 * day) + _hex("#EEF6F6") * .7 * day, col)
        tw = np.clip(1 - np.abs(lam) / .14, 0, 1)[..., None] * (Rs < 300)           # dusk band
        col = col * (1 - tw * .5) + pal.ramp("accent", .3) * tw * .5
        if 14 < Rs < 140:                                                       # city lights on the night side
            g = _h(np.round(lon * 34), np.round(lat * 34), 4.2)
            city = land & (lam < -.05) & (g > .8) & ~ice
            col = np.where(city[..., None], pal.ramp("energy", .7 + .3 * (g > .93)), col)
        sub = cv.rgb[b]
        cv.rgb[b] = np.where(inside[..., None], col, sub)
        th = float(np.clip(.07 * Rs, 1.5, 3.5)) / Rs                           # atmosphere: a thin rim, never a band
        rim = (d > 1.0) & (d < 1.0 + th)
        ra = np.clip(1 - (d - 1) / th, 0, 1) * (.15 + .75 * np.clip(lam * 1.4 + .3, 0, 1)) * (.35 if Rs > 200 else 1.0)
        cv.rgb[b] = np.where(rim[..., None], sub * (1 - ra[..., None]) + _hex("#5FD6F0") * ra[..., None], cv.rgb[b])
        edge = inside & (d > 1 - max(.02, 1.0 / Rs)) & (lam > -.25) & (Rs < 150)
        cv.rgb[b] = np.where(edge[..., None], _hex("#5FD6F0"), cv.rgb[b])

    # ---- stage 0: the kid on the hill
    def _kid_frame(self, B, lb):
        p = self.p
        if p["rewind_to_frame0"] and p.get("rewind_turn"):
            # the loop segment starts on the S9 close-up pose (front) and turns back up to the telescope (frame 0)
            t0, t1 = p["rewind_turn"]
            if lb < t0: return "front"
            if lb < t1: return "q"
        if p["kid_turns"]:
            u = (lb - p["turn_at"]) / max(p["turn_beats"], 1e-6)
            if u < .35: f = "up"
            elif u < .8: f = "q"
            else:
                g = lb - p["eye_glint_at"]
                f = "wow" if -.5 <= g < 1.25 else "front"
                if f == "front" and (lb % 3.1) > 2.95: f = "front_blink"
            return f
        per = (self.total or 80) / max(1, round((self.total or 80) / 3.4))
        return "up_blink" if (B % per) > per - .14 else "up"

    def _surf(self, x):
        return HILL_R - np.sqrt(np.maximum(HILL_R ** 2 - np.asarray(x, float) ** 2, 0)) + 14

    def _hill_top(self, x):
        x = np.asarray(x, float)
        return self._surf(x) - 15.5 * np.exp(-(x / 44.0) ** 2) - 26 * np.exp(-((x + 70) / 24.0) ** 2) \
            - 9 * np.exp(-((x - 88) / 30.0) ** 2)

    def _kid_stage(self, cv, B, lb, atm, frame="up", close=False):
        pal = cv.pal; p = self.p
        xs = np.arange(-200, 201, 2.5); surf = self._surf(xs)
        # far ridge + town lights (sits on the planet's surface)
        ridge = surf - 8 - 4 * np.sin(xs * .045 + 1.3) - 2.5 * np.sin(xs * .13)
        cv.poly(list(zip(xs, ridge)) + list(zip(xs[::-1], surf[::-1] + 2)), pal.ramp("bg", .5), 1.0)
        for x, r in self.towns:
            y = float(np.interp(x, xs, ridge)) + 1.5 + 3 * r
            on = .55 + .45 * math.sin(self.ph(B, 9 + 6 * r, r * 9))
            cv.points(np.array([x]), np.array([y]), pal.ramp("energy", .7 + .3 * r), .5 + .5 * on)
        # near hills with moon-rim light + grass
        top = self._hill_top(xs)
        cv.poly(list(zip(xs, top)) + list(zip(xs[::-1], surf[::-1] + 2)), pal.ramp("bg", .72), 1.0)
        cv.polyline(list(zip(xs, top + .2)), .45, flat=pal.ramp("body", .42), alpha=.9)
        gx = self.grass; gy = self._hill_top(gx)
        sway = .45 * np.sin(self.ph(B, 6) + gx * .17) + .25 * np.sin(self.ph(B, 2.5) + gx * .5)
        ok = np.abs(gx) < 160
        for x, y, h, w in zip(gx[ok], gy[ok], self.grass_h[ok], sway[ok]):
            cv.line(float(x), float(y) + .3, float(x + w * h * .5), float(y - h), .5, pal.ramp("body", .3), .95)
        # telescope behind the kid's arm, kid, then the telescope tube in front of the face
        sc = float(p["kid_scale"]); kx = 0.0
        tri = (8.5 * sc, -7.0 * sc)
        for fx, fy in ((4.4 * sc, 1.0), (12.6 * sc, 1.6), (9.2 * sc, 3.0)):
            cv.line(tri[0], tri[1], fx, fy, .45 * sc, pal.ramp("pale", .42), 1.0)
        draw_kid(cv, frame, kx, 1.2, sc)
        look_up = not close or frame in ("up", "up_blink")
        a0 = (5.4 * sc, -12.4 * sc) if look_up else (7.6 * sc, -9.8 * sc)
        a1 = (15.8 * sc, -23.0 * sc)
        mid = (a0[0] * .45 + a1[0] * .55, a0[1] * .45 + a1[1] * .55)
        cv.capsule(*a0, *mid, .62 * sc, ramp="body", light=(-.4, -.8), tone=1.0)
        cv.capsule(*mid, *a1, .86 * sc, ramp="body", light=(-.4, -.8), tone=1.05)
        cv.line(mid[0] - .7 * sc, mid[1] + .2 * sc, mid[0] + .3 * sc, mid[1] + 1.0 * sc, .4 * sc, pal.ramp("energy", .75), 1.0)
        cv.disc(a0[0], a0[1], .55 * sc, pal.ramp("energy", .7), 1.0)
        ex_, ey_ = a1[0] + .35 * sc, a1[1] - .35 * sc
        cv.ellipse(ex_, ey_, 1.05 * sc, .8 * sc, pal.ramp("energy", .8), 1.0, ang=-.8)
        cv.ellipse(ex_ + .1 * sc, ey_ - .1 * sc, .72 * sc, .52 * sc, pal.ramp("pale", .75), 1.0, ang=-.8)
        cv.points(np.array([ex_ + .3 * sc]), np.array([ey_ - .35 * sc]), _hex("#EEF6F6"), 1.0)
        cv.glow(ex_, ey_, 1.6 * sc, pal.ramp("pale", .9), .18)
        # foreground tufts in the bottom corners (decor only: nothing readable in the UI zone)
        for side in (-1, 1):
            for k in range(9):
                bx = side * (58 + k * 4.2); by = 60.0 + (k % 3) * 2.5
                h = 9 + (k * 7) % 6; w = .5 * math.sin(self.ph(B, 6) + bx * .2)
                cv.line(bx, by, bx + side * .6 + w * h * .3, by - h, 1.2, pal.ramp("bg", .25), 1.0)
                cv.line(bx + side * .4, by - h * .55, bx + side * .6 + w * h * .3, by - h, .5, pal.ramp("body", .3), .9)
        for x0, y0, ph, rr in self.flies:
            a = self.ph(B, 16, ph); x = x0 + rr * math.sin(a); y = y0 - 10 + 3 * math.sin(2 * a + ph)
            on = .5 + .5 * math.sin(self.ph(B, 3.3, ph * 3))
            if on > .25:
                cv.glow(x, y, 2.2, pal.ramp("energy", .8), .35 * on)
                cv.points(np.array([x]), np.array([y]), pal.ramp("energy", 1.0), on)
        if close:
            g = lb - p["eye_glint_at"]
            if -.05 <= g < 1.0 and frame == "wow":
                k = smooth(g, 0, .2) * (1 - smooth(g, .7, 1.0))
                ex, ey = kx + 4 * sc, 1.2 - (24 - 11) * sc                  # the kid's eye on the screen-right side
                cv.points(np.array([ex - .4]), np.array([ey - .6]), _hex("#EEF6F6"), k)
                cv.glow(ex + 7, ey - 9, 4.5, pal.ramp("energy", .8), .55 * k)
                draw_mark(cv, pal, ex + 7, ey - 9, .44, alpha=k, glow=0, snap=True)

    # ---- the kid's sky: equations as constellations
    def _const_paths(self):
        if getattr(self, "_cp", None) is not None: return self._cp
        out = []; ys = self.p.get("const_y") or [cy for _, cy, _ in EQUATIONS]   # const_y: per-equation centre y override
        for (toks, _, h), cy in zip(EQUATIONS, ys):
            u = h / 6.0; widths = [(4 * sc + 2.2) * u for _, sc, _ in toks]; W = sum(widths) - 2.2 * u
            x = -W / 2
            for (ch, sc, dy), w in zip(toks, widths):
                for stroke in STROKE[ch]:
                    out.append([(x + px * u * sc, cy - h / 2 + (py * sc + dy) * u) for px, py in stroke])
                x += w
        self._cp = out; return out

    def _constellations(self, cv, B, lb):
        pal = cv.pal; paths = self._const_paths()
        lens = [sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(s[:-1], s[1:])) for s in paths]
        total = sum(lens); prog = smooth(lb, self.p["draw_at"], self.p["draw_at"] + self.p["draw_beats"])
        prog = (lb - self.p["draw_at"]) / self.p["draw_beats"]; prog = min(max(prog, 0.0), 1.0)
        L = total * prog; done = 0.0
        for s, ln in zip(paths, lens):
            for a, b in zip(s[:-1], s[1:]):
                seg = math.hypot(b[0] - a[0], b[1] - a[1])
                if L > done:
                    f = min(1.0, (L - done) / max(seg, 1e-6))
                    cv.line(a[0], a[1], a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, .7, pal.ramp("pale", .62), .8)
                done += seg
        done = 0.0; seen = set()
        for s in paths:
            for k, (x, y) in enumerate(s):
                if k: done += math.hypot(x - s[k - 1][0], y - s[k - 1][1])
                key = (round(x, 1), round(y, 1))
                if key in seen: continue
                seen.add(key)
                lit = L >= done - 1e-6
                tw = .7 + .3 * math.sin(self.ph(B, 3 + (hash(key) % 5)) + x)
                pop = math.exp(-max(0.0, (L - done)) / 6.0) if lit else 0.0
                c = pal.ramp("energy", .95) if lit else pal.ramp("pale", .7)
                cv.points(np.array([x]), np.array([y]), c, (1.0 if lit else .55) * tw)
                if lit:
                    cv.glow(x, y, 1.6 + 2.5 * pop, pal.ramp("energy", .8), .35 + .5 * pop)
                    for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        cv.points(np.array([x + ox / cv.cam.zoom]), np.array([y + oy / cv.cam.zoom]), c, .35 * tw)


SCENES["cosmic_zoom"] = CosmicZoom


# ================================================================================================ galaxy chess
def rule_ca(rule=30, w=8, gens=16, start=None, wrap=True):
    """elementary cellular automaton (Wolfram code `rule`), single live cell at `start` (default w//2).
    → uint8 array (gens, w)."""
    c = np.zeros(w, np.uint8); c[w // 2 if start is None else start] = 1; out = np.zeros((gens, w), np.uint8)
    for g in range(gens):
        out[g] = c
        l = np.roll(c, 1); r = np.roll(c, -1)
        if not wrap: l[0] = 0; r[-1] = 0
        c = ((rule >> (l * 4 + c * 2 + r)) & 1).astype(np.uint8)
    return out


OPENING = [("e2", "e4"), ("e7", "e5"), ("g1", "f3"), ("b8", "c6"), ("f1", "c4"), ("g8", "f6"), ("d2", "d3"), ("f8", "c5"),
           ("b1", "c3"), ("d7", "d6")]                          # Italian game: quiet, readable slides
BACK = "RNBQKBNR"


def _sq(name):
    return "abcdefgh".index(name[0]), 8 - int(name[1])          # (col, row) with row 0 = top (rank 8)


def draw_galaxy_piece(cv, x, y, kind, side, s, t, alpha=1.0):
    """a chess piece as a tiny galaxy: P dwarf elliptical, R round E0 with halo, N irregular, B edge-on disc,
    Q grand-design spiral, K barred spiral with a ring. side 0 = gold, 1 = violet; s = cell size; t = spin phase."""
    pal = cv.pal; ramp = "energy" if side == 0 else "accent"
    hot = pal.ramp(ramp, .95); mid = pal.ramp(ramp, .7); dim = pal.ramp(ramp, .45)
    k = s / 15.0 * 1.25
    cv.ellipse(x + .6 * k, y + 3.6 * k, 4.2 * k, 1.3 * k, _hex("#04030A"), .55 * alpha)          # contact shadow
    if kind == "P":
        cv.ellipse(x, y, 2.3 * k, 1.9 * k, dim, alpha); cv.ellipse(x, y, 1.3 * k, 1.1 * k, mid, alpha)
        cv.disc(x, y, .6 * k, hot, alpha)
    elif kind == "R":
        cv.disc(x, y, 3.8 * k, dim, .55 * alpha); cv.disc(x, y, 2.8 * k, mid, alpha); cv.disc(x, y, 1.5 * k, hot, alpha)
        cv.ring(x, y, 4.3 * k, .45 * k, mid, .7 * alpha)
    elif kind == "N":
        for dx, dy, r in ((-1.2, .6, 2.0), (1.1, -.9, 1.6), (.4, 1.4, 1.2)):
            cv.disc(x + dx * k, y + dy * k, r * k, dim, alpha)
        cv.disc(x - .6 * k, y + .1 * k, 1.1 * k, mid, alpha); cv.disc(x + 1.0 * k, y - .8 * k, .7 * k, hot, alpha)
    elif kind == "B":
        cv.ellipse(x, y, 4.6 * k, 1.3 * k, dim, alpha, ang=-.5); cv.ellipse(x, y, 3.2 * k, .7 * k, mid, alpha, ang=-.5)
        cv.disc(x, y, 1.2 * k, hot, alpha)
    else:
        n = 2; R = 5.4 * k if kind == "Q" else 5.0 * k
        for arm in range(n):
            for j in range(16):
                u = j / 15.0; a = t + arm * math.pi + u * 3.4; r = (.25 + .75 * u) * R
                px, py = x + r * math.cos(a), y + r * math.sin(a) * .78
                cv.points(np.array([px]), np.array([py]), mid if u < .6 else dim, alpha * (1 - .5 * u))
        if kind == "K":
            ca, sa = math.cos(t), math.sin(t)
            cv.line(x - 2.2 * k * ca, y - 2.2 * k * sa * .78, x + 2.2 * k * ca, y + 2.2 * k * sa * .78, .9 * k, mid, alpha)
            cv.ring(x, y, 3.0 * k, .4 * k, dim, .8 * alpha)
        cv.disc(x, y, 1.6 * k, mid, alpha); cv.disc(x, y, .9 * k, hot, alpha)
    cv.glow(x, y, 4.5 * k, hot, .16 * alpha)


class GalaxyChess(_Loop, Scene):
    """8×8 board of the cosmos (cells c1/c2) with galaxy chess pieces playing an opening (one move every `move_every`
    beats) while an elementary CA (rule `ca_rule`) lights one generation per row. The CA is SYNCED to the music: with
    `ca_series` (default "kural30" when spec.music.series_defs has it) each lit cell appears exactly when its note plays
    (gen g = notes 4g..4g+3 of the series voice; value = the cell column), so the board is the score. Without a series
    it runs on its own every `ca_row_every` beats.
    zoom_out_boards: every square is itself a board — the scene pulls back `levels` powers of 8 (per-pixel LOD
    renderer of a 512-wide rule-30 universe with the live board at its apex), boards of boards with their own pieces.
    far_ca / far_dots (.55 / .9): strength of the CA light and of the piece dots on the boards of boards (lower = calmer).
    counter {from, to, beats, hold, xy}: screen-fixed "10ⁿ" rolling from→to over `beats` (superscript pixfont, in the
    caption box + highlight colour), held `hold` beats so a title block with the same text can take over seamlessly."""
    own_layers = 2                    # spinning galaxy pieces + the CA light field / board-of-boards zoom
    defaults = {"pieces": "galaxies", "ca_rule": 30, "ca_row_every": 1.0, "ca_series": "kural30", "ca_voice": None,
                "notes_per_gen": 4, "move_every": 2.0, "first_move": .5, "board_xy": [0.0, -25.0], "cell": 15.0,
                "c1": "#140F38", "c2": "#1F1752", "zoom_out_boards": False, "levels": 1.86, "zoom_beats": [1.0, -1.5],
                "counter": None, "moves_done": 0, "focus_sq": "d5", "seed_world": 30, "far_ca": .55, "far_dots": .9}

    def on_bind(self):
        self.lights = None

    def bind(self, seg, spec):
        super().bind(seg, spec)
        p = self.p; m = spec.get("music") or {}; sd = (m.get("series_defs") or {}).get(p["ca_series"])
        self.lights = None
        if sd:
            vname, rate, phase = p.get("ca_voice"), 4.0, "section"
            for nm, v in (m.get("voices") or {}).items():
                ss = (v or {}).get("series") or {}
                if ss.get("name") == p["ca_series"] and (vname is None or nm == vname) and not ss.get("offset"):
                    vname, rate, phase = nm, float(ss.get("rate", 4)), ss.get("phase", "section"); break
            sec = next((s for s in spec.get("_sections", []) if s["b0"] <= self.b0 + 1e-6 < s["b1"]), None)
            if sec is not None:
                vals = sd["values"]; per = int(sd.get("period", len(vals))); npg = int(p["notes_per_gen"])
                n = int(math.ceil(sec["b0"] * rate - 1e-9)); n0 = n if phase == "section" else 0
                ev = []
                while n / rate < self.b0 + self.dur - 1e-9:
                    if n / rate >= self.b0 - 1.0:
                        i = n - n0; ev.append((n / rate, (i // npg) % 8, int(vals[i % per]) % 8, i // npg))
                    n += 1
                self.lights = ev; self.sec_b0 = sec["b0"]; self.rate = rate
        return self

    def setup(self):
        p = self.p
        self.ca = rule_ca(int(p["ca_rule"]), 8, 64)
        if p["zoom_out_boards"]:
            big = rule_ca(int(p["ca_rule"]), 512, 512, start=260, wrap=False).astype(np.float32)
            self.D = [big, big.reshape(64, 8, 64, 8).mean((1, 3)), big.reshape(8, 64, 8, 64).mean((1, 3)),
                      np.full((1, 1), big.mean(), np.float32)]

    # ------------------------------------------------------------------ timeline
    def _cell_light(self, lb):
        """→ (8, 8) brightness of the lit cells at local beat lb (flash on note, steady, older generations dim)."""
        L = np.zeros((8, 8), np.float32); B = self.gbeat(lb)
        if self.lights is not None:
            cur = None
            for b, row, col, g in self.lights:
                if b <= B + 1e-6: cur = g
            if cur is None: return L
            for b, row, col, g in self.lights:
                if b > B + 1e-6 or g < cur - 7: continue
                age = cur - g; fl = max(0.0, 1 - (B - b) / .35)
                L[row, col] = max(L[row, col], (1 - .09 * age) * .75 + .6 * fl)
        else:
            ge = self.p["ca_row_every"]; cur = int(lb // ge)
            for g in range(max(0, cur - 7), cur + 1):
                fl = max(0.0, 1 - (lb - g * ge) / .35)
                L[g % 8] = np.maximum(L[g % 8], self.ca[g] * ((1 - .09 * (cur - g)) * .75 + .6 * fl))
        return L

    def _pieces(self, lb):
        """→ list of (kind, side, col, row) with fractional positions for sliding pieces"""
        p = self.p; pos = {}
        for c, k in enumerate(BACK):
            pos[(c, 7)] = (k, 0); pos[(c, 0)] = (k, 1); pos[(c, 6)] = ("P", 0); pos[(c, 1)] = ("P", 1)
        out = []; moving = {}
        done = int(p["moves_done"])
        for i, (a, b) in enumerate(OPENING):
            t0 = p["first_move"] + (i - done) * p["move_every"] if i >= done else -1e9
            if lb < t0: break
            fa, fb = _sq(a), _sq(b); pc = pos.pop(fa)
            k = smooth(lb, t0, t0 + .7) if t0 > -1e8 else 1.0
            if k < 1: moving[fb] = (pc, fa, k)
            pos[fb] = pc
        for (c, r), (kind, side) in pos.items():
            if (c, r) in moving:
                _, fa, k = moving[(c, r)]; k = ease(k, "inOutCubic")
                out.append((kind, side, fa[0] + (c - fa[0]) * k, fa[1] + (r - fa[1]) * k, 1 - abs(2 * k - 1)))
            else: out.append((kind, side, float(c), float(r), 0.0))
        return out

    def focus(self, lb, dur_b):
        c, r = _sq(self.p["focus_sq"]); bx, by = self.p["board_xy"]; cs = self.p["cell"]
        return bx + (c - 3.5) * cs, by + (r - 3.5) * cs

    # ------------------------------------------------------------------ draw
    def draw(self, cv, lt, lb, dur_b):
        p = self.p; B = self.gbeat(lb)
        if p["zoom_out_boards"]: self._universe(cv, lb, dur_b)
        else: self._board(cv, lb, p["board_xy"], p["cell"])
        if p.get("counter"): self._counter(cv, lb)

    def _board(self, cv, lb, xy, cs, alpha=1.0):
        pal = cv.pal; bx, by = xy; c1, c2 = _hex(self.p["c1"]), _hex(self.p["c2"])
        hw = cs * 4
        cv.glow(bx, by, hw * 1.6, pal.ramp("body", .5), .12)
        cv.rect(bx, by + 2.5, 8 * cs + 7, 8 * cs + 7, _hex("#04030A"), .7)
        cv.rect(bx, by, 8 * cs + 6, 8 * cs + 6, pal.ramp("energy", .25), 1.0)
        cv.rect(bx, by, 8 * cs + 3, 8 * cs + 3, pal.ramp("energy", .45), 1.0)
        L = self._cell_light(lb); lit = pal.ramp("pale", .82)
        for r in range(8):
            for c in range(8):
                x = bx + (c - 3.5) * cs; y = by + (r - 3.5) * cs
                cv.rect(x, y, cs, cs, c1 if (r + c) % 2 == 0 else c2, 1.0)
                if L[r, c] > 0:
                    a = min(1.0, L[r, c])
                    cv.rect(x, y, cs - 1.5, cs - 1.5, lit, .55 * a); cv.rect(x, y, cs - 5, cs - 5, lit, .45 * a)
                    cv.glow(x, y, cs * .8, lit, .18 * a)
        # subtle nebula sparkle in the dark squares (cosmos, not wood)
        rng = np.random.default_rng(int(self.p["seed_world"]))
        sx = bx + rng.uniform(-hw, hw, 90); sy = by + rng.uniform(-hw, hw, 90); ph = rng.random(90)
        tw = .3 + .3 * np.sin(self.ph(self.gbeat(lb), 2.4, 0) + ph * TAU)
        cv.points(sx, sy, pal.ramp("pale", .6), tw)
        spin = self.ph(self.gbeat(lb), 12.0)
        for kind, side, c, r, lift in sorted(self._pieces(lb), key=lambda q: q[3]):
            x = bx + (c - 3.5) * cs; y = by + (r - 3.5) * cs - lift * cs * .35
            if lift > 0:
                cv.glow(x, y, cs * .7, pal.ramp("energy" if side == 0 else "accent", .8), .25 * lift)
            draw_galaxy_piece(cv, x, y, kind, side, cs, spin * (1 if side == 0 else -1) + c * .7 + r, alpha)

    # ------------------------------------------------------------------ board of boards (S7)
    def _zc(self, lb, dur_b):
        a, b = self.p["zoom_beats"]; b = b if b > 0 else dur_b + b
        return self.p["levels"] * ease(min(max((lb - a) / max(b - a, 1e-6), 0.0), 1.0), "inOutSine")

    def _universe(self, cv, lb, dur_b):
        p = self.p; pal = cv.pal; cs0 = p["cell"]; Zc = self._zc(lb, dur_b); c = cs0 / 8 ** Zc
        bx, by = p["board_xy"]; Lend = p["levels"]
        kk = (8 ** Zc - 1) / (8 ** Lend - 1)
        Px, Py = bx, by - 252.0 * c * kk                       # main board centre drifts so the 512-grid ends centred
        f = c * cv.cam.zoom                                   # fine cell size in px
        wx, wy = cv.world_grid()
        X = 260.0 + (wx - Px) / c; Y = 4.0 + (wy - Py) / c
        inside = (X >= 0) & (X < 512) & (Y >= 0) & (Y < 512)
        Xi = np.clip(X, 0, 511.999).astype(np.int32); Yi = np.clip(Y, 0, 511.999).astype(np.int32)
        c1, c2 = _hex(p["c1"]), _hex(p["c2"]); lit = pal.ramp("pale", .82)
        # LOD level: smallest level whose cells are >= 2 px, blended over one octave of 8
        lv = np.log(2.0 / f) / np.log(8.0); L0 = int(np.clip(math.floor(lv) + 1, 0, 3)) if lv > 0 else 0
        t = float(np.clip((lv - (L0 - 1)), 0, 1)) if lv > 0 else 0.0
        def level_rgb(L):
            s = 8 ** L; cx_ = np.floor(X / s); cy_ = np.floor(Y / s)
            par = ((cx_ + cy_) % 2 == 0)[..., None]
            tint = (.9 + .1 * L)
            base = np.where(par, c1, c2) * tint
            if L == 0: d = self.D[0][Yi, Xi]
            elif L <= 2: d = self.D[L][Yi // s, Xi // s]
            else: d = np.full(X.shape, float(self.D[3][0, 0]), np.float32)
            rev = np.clip((8.0 * 8 ** (Zc + .25) - Y) / (6.0 / max(f, 1e-3)), 0, 1)   # the universe "computes" downward
            d = d * rev * inside
            w = float(p["far_ca"]) * d[..., None]                # far_ca: how loud the CA light is on the boards of boards
            return base * (1 - w) + lit * w
        col = level_rgb(L0)
        if 0 < t < 1 and L0 > 0: col = level_rgb(L0 - 1) * (1 - t) + col * t
        # pieces of every other board: start position dots (rows 0,1 violet / 6,7 gold) once cells are ≥ 1 px
        if f >= 2.5:
            lx = X - np.floor(X / 8) * 8; ly = Y - np.floor(Y / 8) * 8
            rr = np.floor(ly); dx = lx - np.floor(lx) - .5; dy = ly - rr - .5
            near = (dx * dx + dy * dy) < .06
            gold = near & ((rr == 6) | (rr == 7)) & inside; vio = near & ((rr == 0) | (rr == 1)) & inside
            pa = smooth(f, 2.5, 4.5) * float(p["far_dots"])
            col = np.where(gold[..., None], col * (1 - pa) + pal.ramp("energy", .8) * pa, col)
            col = np.where(vio[..., None], col * (1 - pa) + pal.ramp("accent", .65) * pa, col)
        # board frames: level-1 (each 8×8 board) and level-2 (boards of boards) seams in dim gold
        for Ls, need, a in ((8, 10.0, .4), (64, 9.0, .45)):
            if f * Ls >= need:
                ex = np.minimum(X % Ls, Ls - X % Ls) * f; ey = np.minimum(Y % Ls, Ls - Y % Ls) * f
                edge = ((ex < .55) | (ey < .55)) & inside
                aa = a * float(np.clip((f * Ls - need) / need, 0, 1))
                col = np.where(edge[..., None], col * (1 - aa) + pal.ramp("energy", .3 if Ls == 8 else .5) * aa, col)
        out = ~inside
        a_out = np.clip(1 - np.maximum(np.maximum(-X, X - 512), np.maximum(-Y, Y - 512)) * f / 40.0, 0, 1) * .45
        nb = smooth(Zc, .02, .45)                                  # neighbour boards fade in as the pull-back starts
        dmain = np.maximum(np.maximum(256 - X, X - 264), np.maximum(-Y, Y - 8))      # cells outside the live board
        a_in = np.clip(nb * 1.6 - np.clip(dmain, 0, None) / 64.0 * (1 - nb), 0, 1)
        a_in = np.where(dmain <= 0, 1.0, a_in)
        m = (inside | (a_out > 0))
        blend = (np.where(out, a_out * nb, a_in))[..., None]
        cv.rgb[m] = (cv.rgb * (1 - blend) + col * blend)[m]
        # the live board (music-synced CA + galaxy pieces) drawn on top while its cells are big enough
        ba = smooth(f, 1.2, 3.0)
        if ba > 0:
            if ba < 1: dither_draw(cv, ba, lambda: self._board(cv, lb, (Px, Py), c))
            else: self._board(cv, lb, (Px, Py), c)
        cv.glow(Px, Py, 8 * c * 1.4, pal.ramp("energy", .7), .12 + .1 * smooth(Zc, .5, 1.5))

    def _counter(self, cv, lb):
        cfg = self.p["counter"]; a, b, nb = cfg.get("from", 1), cfg.get("to", 120), cfg.get("beats", 4)
        if lb > nb + float(cfg.get("hold", 0.0)) + .02: return
        k = ease(min(max(lb / nb, 0.0), 1.0), "inCubic") if cfg.get("ease", True) else min(lb / nb, 1.0)
        n = int(round(a + (b - a) * k))
        xy = cfg.get("xy", [0.5, 0.2])
        base = cv.cam; cv.set_cam(Camera(0, 0, 1, 0))
        X = (xy[0] - .5) * cv.W; Y = (xy[1] - .5) * cv.H
        before = cv.rgb.copy()
        txt = "10" + str(n).translate(SUPERSCRIPT)
        cap = getattr(cv.pal, "caption", None) or {}
        hi = np.array(cap.get("hi", (65, 232, 210)), np.float32) / 255; box = np.array(cap.get("box", (4, 6, 14)), np.float32) / 255
        tw_ = text_bitmap(txt).shape[1] * 2
        cv.rect(X, Y, tw_ + 8, 24, box, 1.0)                     # same box + highlight colour as the title it hands over to
        draw_text(cv, txt, X, Y, 2.0, hi, 1.0, snap=True)
        ch = np.abs(cv.rgb - before).max(-1) > 2e-3          # legible: exempt from glow + vignette
        cv.glowbuf[ch] = 0; cv.keep = ch if getattr(cv, "keep", None) is None else (cv.keep | ch)
        cv.set_cam(base)


SCENES["galaxy_chess"] = GalaxyChess
