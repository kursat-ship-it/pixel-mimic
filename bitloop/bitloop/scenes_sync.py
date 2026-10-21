"""pendulum_grid: 99 Kuramoto-coupled pendulums in a rows×cols grid.

One clock: the phase of every pendulum is a pure function of the GLOBAL beat (self.b0 + lb), so consecutive
segments are one continuous world and the loop seam is exact (the composition freezes, then the loop dissolve
returns to frame 0's chaos). Synchronisation = the order parameter rising: the initial phase spread collapses to a
common swing, while one detuned oscillator (17:16 natural frequency) keeps drifting and stays out of lock. A coral
ring locks it at the reveal, the order-parameter formula R(t)=|Σe^{iφ_j}|/99 appears, and the last beat freezes.

Palette (Çini Gecesi): dark navy backdrop (bg), thin Sis strings, cream bobs (pale), türkuaz light trails (energy),
the single outlier highlighted with the rare warm coral (accent) — exactly how the brand reserves coral."""
import math
import numpy as np
from .scenes import Scene, pulse, TAU


def _smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3.0 - 2.0 * x)


class PendulumGrid(Scene):
    defaults = {
        "rows": 11, "cols": 9,
        "outlier": 49, "freq_ratio": 17.0 / 16.0,
        "period_beats": 4.0, "amp": 0.75, "string": 11.0,
        "sync_start": 3.0, "sync_end": 24.0,
        "wave_start": 12.0, "wave_end": 18.0, "wave_amp": 0.55,
        "trail": 5, "bloom": 0.8,
        "outlier_ring": {"at": 26.0, "beats": 1.0},
        "formula": {"text": "R(t) = |Σ e^(iφj)| / 99", "at": 28.0, "dot": 1.0, "y": 94.0},
        "freeze": {"at": 29.0, "beats": 1.0},
    }

    def setup(self):
        p = self.p
        self.rows, self.cols = int(p["rows"]), int(p["cols"])
        self.n = self.rows * self.cols
        # deterministic initial phases (NO per-segment RNG): every segment instance sees the same world
        idx = np.arange(self.n, dtype=np.float64)
        self.phi0 = 2.0 * math.pi * ((idx * 0.6180339887498949 + idx * idx * 0.00103 + 0.371) % 1.0)
        self.colx = -80.0 + 20.0 * np.arange(self.cols)
        self.rowy = -95.0 + 14.0 * np.arange(self.rows)
        self.gx = (np.arange(self.cols) - (self.cols - 1) / 2.0) / max(self.cols - 1, 1)
        self.gy = (np.arange(self.rows) - (self.rows - 1) / 2.0) / max(self.rows - 1, 1)
        self._sample = [i for i in (7, 17, 29, 41, 61, 73) if i < self.n]

    # ------------------------------------------------------------------ physics (pure functions of global beat)
    def _omega(self):
        return TAU / self.p["period_beats"]

    def _sync(self, gb):
        p = self.p
        return _smooth((gb - p["sync_start"]) / max(p["sync_end"] - p["sync_start"], 1e-9))

    def _wave(self, gb, c, r):
        """Three sequential travelling ripples (horizontal → vertical → diagonal) during the 'waves' phase."""
        p = self.p
        xj, yj = self.gx[c], self.gy[r]
        ws, we = p["wave_start"], p["wave_end"]
        u = (gb - ws) / max(we - ws, 1e-9)
        if not (0.0 < u < 1.0):
            return 0.0
        env = math.sin(math.pi * u) ** 2
        if u < 1.0 / 3.0:
            m = math.sin(TAU * (0.5 + 0.5 * xj) - TAU * gb / 2.0)
        elif u < 2.0 / 3.0:
            m = math.sin(TAU * (0.5 + 0.5 * yj) - TAU * gb / 2.0)
        else:
            m = math.sin(TAU * (0.5 + 0.25 * (xj + yj)) - TAU * gb / 2.0)
        return p["wave_amp"] * env * m

    def _phase(self, gb, j):
        """Swing phase of pendulum j at global beat gb. Synchronised pendulums collapse their initial spread as
        the coupling rises; the outlier keeps its own (17:16) natural frequency and never locks."""
        p = self.p
        if j == p["outlier"]:
            return self._omega() * p["freq_ratio"] * gb + self.phi0[j]
        c = j % self.cols; r = j // self.cols
        s = self._sync(gb)
        return self._omega() * gb + self.phi0[j] * (1.0 - s) ** 2 + self._wave(gb, c, r)

    # ------------------------------------------------------------------ draw
    def draw(self, cv, lt, lb, dur_b):
        p = self.p
        gb = min(self.b0 + lb, float(p["freeze"]["at"]))      # freeze the composition at the end
        L, amp = p["string"], p["amp"]
        beam = self.pal.ramp("dim", 0.5)
        for r in range(self.rows):
            cv.line(-82, self.rowy[r], 82, self.rowy[r], 0.8, beam, 0.5)
        for r in range(self.rows):
            for c in range(self.cols):
                j = r * self.cols + c
                px, py = self.colx[c], self.rowy[r]
                th = self._phase(gb, j)
                ang = amp * math.sin(th)
                bx = px + L * math.sin(ang)
                by = py + L * math.cos(ang)
                cv.line(px, py, bx, by, 0.6, self.pal.ramp("pale", 0.5), 0.55)
                for q in range(1, int(p["trail"]) + 1):      # türkuaz light trails (ghost bobs)
                    gb2 = max(gb - 0.12 * q, 0.0)
                    th2 = self._phase(gb2, j)
                    a2 = amp * math.sin(th2)
                    cv.disc(px + L * math.sin(a2), py + L * math.cos(a2), 1.0,
                            self.E(0.7), 0.45 * (1.0 - q / (p["trail"] + 1.0)))
                cv.disc(bx, by, 1.6, self.pal.ramp("pale", 0.95), 1.0)
                cv.glow(bx, by, 2.8, self.pal.ramp("pale", 1.0), p["bloom"] * 0.5)
        # coral ring locks the outlier (rare warm colour = the one exception)
        o = p["outlier"]
        if gb >= float(p["outlier_ring"]["at"]):
            c = o % self.cols; r = o // self.cols
            px, py = self.colx[c], self.rowy[r]
            th = self._phase(gb, o); ang = amp * math.sin(th)
            bx = px + L * math.sin(ang); by = py + L * math.cos(ang)
            pk = pulse(gb, 1.0, 5.0)
            R = 5.0 + 3.2 * pk
            cv.glow(bx, by, R * 2.1, self.A(0.85), 0.6 + 0.9 * pk)
            cv.ring(bx, by, R, 2.1, self.A(0.92), 1.0)          # vivid coral ring (the one warm accent)
            cv.ring(bx, by, R * 1.45, 1.0, self.A(0.7), 0.5)     # faint outer halo
        if gb >= float(p["formula"]["at"]):
            self._formula(cv)

    def _formula(self, cv):
        """R(t) = |Σ e^(iφj)| / 99 — one snapped line (pixel-exact; the caret stands in for the superscript)."""
        from .bitmap import draw_text
        p = self.p["formula"]; dot = float(p["dot"]); y = float(p.get("y", 94.0))
        draw_text(cv, "R(t) = |Σ e^(iφj)| / 99", 0.0, y, dot, self.pal.ramp("pale", 0.95), snap=True)

    # ------------------------------------------------------------------ sound: ticks = pendulum peaks
    def sfx(self, dur_b):
        p = self.p
        out = []
        # outlier: its own (17:16) drifting peaks, a semitone up (tick_hi), always audible
        o = p["outlier"]; wo = self._omega() * p["freq_ratio"]; ph0 = self.phi0[o]
        m = 0
        while True:
            gb = (math.pi / 2.0 + m * math.pi - ph0) / wo
            lb = gb - self.b0
            if lb >= dur_b: break
            if 0.0 <= lb: out.append((round(lb, 3), "tick_hi"))
            m += 1
        # group: chaotic polyrhythm (scattered sample peaks) → one coherent tick per half-period as R rises
        half = p["period_beats"] / 2.0
        k = 0
        while True:
            gb = 1.0 + 2.0 * k                                  # mean-field peaks (period_beats=4 → odd beats)
            lb = gb - self.b0
            if lb >= dur_b: break
            if 0.0 <= lb:
                if self._sync(gb) > 0.30:
                    out.append((round(lb, 3), "tick"))
                else:
                    for q, si in enumerate(self._sample):       # scatter by each sample's initial phase
                        off = (self.phi0[si] / TAU) * half * 0.8
                        ob = lb + off
                        if 0.0 <= ob < dur_b: out.append((round(ob, 3), "tick"))
            k += 1
        out.sort()
        return out


from .scenes import SCENES  # noqa: E402
SCENES.update({"pendulum_grid": PendulumGrid})
