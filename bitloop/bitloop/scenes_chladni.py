"""chladni: sand on a vibrating plate reveals the nodal lines of a standing wave. The pattern is a pure function of
time and mode (n,m): particles are seeded once (deterministic) and, each frame, pulled toward the nearest nodal line by
a settle factor, so the sand "flees the vibrating places" and collects on the nodes. The plate mode order (n²+m²)
rises with the driving tone, so the shape you see and the pitch you hear come from the same resonance.

Idealised simply-supported square plate: w(u,v) = cos(nπu)·cos(mπv); nodal lines at u=(2k+1)/(2n) and v=(2l+1)/(2m).
(Real free-edge plates have curved modes, but the nodal-line structure — the Chladni figure — is qualitatively the same.)"""
import math
import numpy as np
from .scenes import Scene, ease, pulse, TAU


class Chladni(Scene):
    own_layers = 3
    defaults = {
        "n": 1, "m": 1,
        "x": 0.0, "y": 0.0, "w": 140.0, "h": 140.0,
        "particles": 1600, "settle_s": 1.1, "jitter": 0.6,
        "freq": 110.0, "label": "", "label_y": -80.0, "label_dot": 1.0,
        "driver": True, "driver_y": 78.0,
    }

    def setup(self):
        p = self.p
        r = self.rng
        n = int(p["particles"])
        # start scattered (uniform over the plate), seeded once — positions are a pure function of t from here
        self.u0 = r.random(n)
        self.v0 = r.random(n)
        self.ph = r.uniform(0, TAU, n)
        self.sz = r.uniform(0.7, 1.3, n)

    def _nodes(self, u, v):
        p = self.p
        n, m = max(1, int(p["n"])), max(1, int(p["m"]))
        # nearest vertical node u*=(2k+1)/(2n) and horizontal v*=(2l+1)/(2m)
        us = (2.0 * np.floor(np.clip(u, 0, 0.999) * n) + 1.0) / (2.0 * n)
        vs = (2.0 * np.floor(np.clip(v, 0, 0.999) * m) + 1.0) / (2.0 * m)
        du, dv = np.abs(u - us), np.abs(v - vs)
        tu = np.where(du < dv, us, u)
        tv = np.where(du < dv, v, vs)
        return tu, tv, np.minimum(du, dv)

    def draw(self, cv, lt, lb, dur_b):
        p, E, pal = self.p, self.E, self.pal
        x0, y0, w, h = p["x"], p["y"], p["w"], p["h"]
        # plate + soft glow
        cv.glow(x0, y0, w * 0.55, E(.35), .20)
        cv.rect(x0, y0, w + 6, h + 6, pal.ramp("dim", .55), 1.0)
        cv.rect(x0, y0, w, h, pal.ramp("bg", .55), 1.0)
        # faint nodal lines (türkuaz) — the hidden geometry, visible from the start
        n, m = max(1, int(p["n"])), max(1, int(p["m"]))
        for k in range(n):
            ux = x0 - w / 2 + (2 * k + 1) / (2 * n) * w
            cv.line(ux, y0 - h / 2, ux, y0 + h / 2, 0.9, pal.ramp("energy", .55), .55)
        for k in range(m):
            vy = y0 - h / 2 + (2 * k + 1) / (2 * m) * h
            cv.line(x0 - w / 2, vy, x0 + w / 2, vy, 0.9, pal.ramp("energy", .55), .55)
        # sand: settle toward the nearest node over settle_s, plus a small deterministic jitter
        settle = ease(min(lt / max(p["settle_s"], 1e-6), 1.0), "outCubic")
        tu, tv, dist = self._nodes(self.u0, self.v0)
        u = self.u0 + (tu - self.u0) * settle
        v = self.v0 + (tv - self.v0) * settle
        jit = p["jitter"] * (1.0 - settle) + 0.15
        u = u + np.sin(lt * 9.0 + self.ph) * jit * 0.004
        v = v + np.cos(lt * 8.0 + self.ph) * jit * 0.004
        px = x0 - w / 2 + np.clip(u, 0, 1) * w
        py = y0 - h / 2 + np.clip(v, 0, 1) * h
        cv.points(px, py, pal.ramp("pale", .85), alpha=.9, size=1)
        hot = dist < 0.02
        if hot.any():
            cv.glow(float(px[hot][0]), float(py[hot][0]), w * .5, E(.45), .06)
        # the driver (a small transducer at the bottom) pulses on the beat
        if p["driver"]:
            dv = pulse(lb, 1.0, 4.0)
            cv.capsule(x0, p["driver_y"] + 8, x0, y0 + h / 2 + 8, 3.0, ramp="dim")
            cv.sphere(x0, p["driver_y"] + 8, 4.0 + 1.5 * dv, "body", rim=E(.6))
            cv.glow(x0, p["driver_y"] + 8, 9 + 6 * dv, E(.8), .4 + .6 * dv)
        if p["label"]:
            from .bitmap import draw_text
            draw_text(cv, p["label"], 0.0, p["label_y"], p["label_dot"], pal.ramp("pale", .95), snap=True)


from .scenes import SCENES  # noqa: E402
SCENES.update({"chladni": Chladni})
