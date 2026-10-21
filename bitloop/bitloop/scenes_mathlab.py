"""formula_scope: a neon XY oscilloscope on a near-black digital-lab grid. Plots y = f(t) (time domain) live from one
of the brief's functions, scrolling right-to-left, with a BLACK tracking dot at the newest sample (magenta halo),
pixel particles bursting on every beat, and the formula drawn small at the bottom.

The curve is computed EXACTLY from the function at every frame (scene-local time t). `own_layers` counts the moving
plot + particles so the brand's >=3-layer rule holds even with a thin backdrop."""
import math
import numpy as np
from .scenes import Scene, pulse, TAU

FORMULA = {
    "hardtekk": {"f": lambda t: 1.0 if (t * 8.0) % 1.0 > 0.9 else -1.0, "amp": 1.0},
    "phonk808": {"f": lambda t: math.sin(TAU * 39 * t) * math.exp(-3 * t) * math.tanh(10 * math.sin(TAU * 0.5 * t)), "amp": 1.0},
    "acid": {"f": lambda t: (1.0 if math.sin(TAU * 4 * t) >= 0 else -1.0) * math.exp(-0.5 * (t % 0.25)), "amp": 1.0},
    "funk": {"f": lambda t: math.sin(TAU * 2 * t) + 0.5 * math.sin(TAU * 6 * t + math.pi / 4), "amp": 1.5},
    "phonkmel": {"f": lambda t: math.sin(TAU * (220 + 50 * math.sin(TAU * 0.3 * t)) * t), "amp": 1.0},
    "jersey": {"f": lambda t: math.sin(TAU * 200 * t) if (t * 12.0) % 1.0 < 0.3 else 0.0, "amp": 1.0},
    "trance": {"f": lambda t: math.sin(TAU * 440 * (2.0 ** ((2 * t) % 1.0)) * t) * math.exp(-2 * (t % 0.5)), "amp": 1.0},
    "psy": {"f": lambda t: math.sin(TAU * 65 * t) * (0.5 + 0.5 * (1.0 if math.sin(TAU * 8 * t) >= 0 else -1.0)), "amp": 1.0},
    "build": {"f": lambda t: math.sin(TAU * (100 + 50 * t) * t) * (min(t, 3.0) / 3.0), "amp": 1.7},
}


class FormulaScope(Scene):
    own_layers = 3
    defaults = {
        "formula": "hardtekk", "amp": None,
        "x": 0.0, "y": 8.0, "w": 150.0, "h": 140.0,
        "window": 0.9, "gain": 1.0, "n": 240,
        "grid": True, "axes": True, "particles": 40,
        "formula_text": "", "formula_y": 92.0, "formula_dot": 1.0,
    }

    def setup(self):
        k = self.p["formula"]
        if k == "all":
            self.FS = [FORMULA[n] for n in ("hardtekk", "phonk808", "acid", "funk", "phonkmel",
                                            "jersey", "trance", "psy", "build")]
            self.amp = float(self.p["amp"] or 1.7)
        else:
            self.FS = [FORMULA.get(k, FORMULA["hardtekk"])]
            self.amp = float(self.p["amp"] or self.FS[0]["amp"])
        r = self.rng
        self.pa = r.uniform(0, TAU, int(self.p["particles"]))
        self.pv = r.uniform(0.4, 1.0, int(self.p["particles"]))

    def _f(self, F, t):
        try:
            return float(F["f"](max(t, 0.0)))
        except Exception:
            return 0.0

    def _map(self, t, y, lt):
        p = self.p
        x0, y0, w, h = p["x"], p["y"], p["w"], p["h"]
        u = (t - (lt - p["window"])) / max(p["window"], 1e-6)
        v = max(-1.0, min(1.0, y / (self.amp * 1.15)))
        return x0 - w / 2 + u * w, y0 - v * h / 2 * p["gain"]

    def draw(self, cv, lt, lb, dur_b):
        p, E, pal = self.p, self.E, self.pal
        x0, y0, w, h = p["x"], p["y"], p["w"], p["h"]
        cv.glow(x0, y0, w * 0.55, E(.5), .16)
        if p["grid"]:
            for gx in np.arange(x0 - w / 2, x0 + w / 2 + .01, w / 8):
                cv.line(gx, y0 - h / 2, gx, y0 + h / 2, 0.6, pal.ramp("dim", .85), .5)
            for gy in np.arange(y0 - h / 2, y0 + h / 2 + .01, h / 8):
                cv.line(x0 - w / 2, gy, x0 + w / 2, gy, 0.6, pal.ramp("dim", .85), .5)
        if p["axes"]:
            cv.line(x0 - w / 2, y0, x0 + w / 2, y0, 1.0, pal.ramp("accent", .7), .85)   # time axis (cyan)
            cv.line(x0, y0 - h / 2, x0, y0 + h / 2, 1.0, pal.ramp("accent", .7), .85)   # y axis
        tt = np.linspace(lt - p["window"], lt, int(p["n"]))
        multi = len(self.FS) > 1
        last = None
        for ci, F in enumerate(self.FS):
            pts = [self._map(t, self._f(F, t), lt) for t in tt]
            last = pts[-1]
            a = .5 if multi else .95
            col = pal.ramp("energy", .92 - .45 * (ci / max(len(self.FS) - 1, 1))) if multi else pal.ramp("energy", .92)
            for (px, py) in pts[::8]:
                cv.glow(px, py, 2.5, E(.85), .12)
            cv.polyline(pts, 1.0 if multi else 1.1, flat=col, alpha=a)
        # black tracking dot with a magenta halo (moves along the curve)
        tx, ty = last
        cv.glow(tx, ty, 5.0, E(.9), .9)
        cv.disc(tx, ty, 1.5, pal.ramp("energy", 1.0), 1.0)
        cv.disc(tx, ty, 1.7, pal.ramp("bg", .15), 1.0)
        # radial particle burst on every beat
        u = lb % 1.0
        for i, a in enumerate(self.pa):
            rad = u * (26 + 34 * self.pv[i])
            px = x0 + math.cos(a) * rad
            py = y0 + math.sin(a) * rad * 0.62
            if abs(px - x0) <= w / 2 + 2 and abs(py - y0) <= h / 2 + 2:
                cv.disc(px, py, 0.8, pal.ramp("energy" if i % 3 else "accent", .9), (1.0 - u) * .8)
        if p["formula_text"]:
            from .bitmap import draw_text
            draw_text(cv, p["formula_text"], 0.0, p["formula_y"], p["formula_dot"],
                      pal.ramp("pale", .95), snap=True)


from .scenes import SCENES  # noqa: E402
SCENES.update({"formula_scope": FormulaScope})
