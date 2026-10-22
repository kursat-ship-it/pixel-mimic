"""Chip voices. Every note is rendered from a per-sample frequency curve (vibrato, sweep, chip-arp, glide), so
pitches may be microtonal. Flavours colour the whole roster:
  2a03   NES: pulse 12.5/25/50 %, 4-bit stepped triangle, LFSR noise, 4-bit volume steps
  gameboy  pulse + 32-step 4-bit wavetable channel, gritty low-passed output
  sid    C64: pulse-width modulation, saw, resonant low-pass filter sweeps, ring-ish detune
  fm     2-operator FM (OPL / Genesis-like): bells, e-pianos, punchy basses
  math   **direct math-to-audio**: evaluates the same f(t) function as the visual (FormulaScope),
         maps y = f(t) → pitch/amplitude for perfect visual-audio sync.
Voice types: pulse, triangle, saw, wave, fm, noise, math."""
import math
import numpy as np

SR = 48000
WAVETABLES = {  # 32 × 4-bit (Game Boy wave channel)
    "bass":  [15, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
    "organ": [8, 12, 15, 15, 12, 8, 5, 4, 6, 9, 12, 13, 12, 9, 6, 4, 4, 6, 9, 12, 13, 12, 9, 6, 4, 5, 8, 12, 15, 15, 12, 8],
    "pluck": [15, 15, 15, 15, 15, 15, 15, 15, 0, 0, 0, 0, 15, 15, 15, 15, 0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 3, 3, 3, 3],
    "soft":  [8, 10, 12, 13, 14, 15, 15, 15, 14, 13, 12, 10, 8, 6, 4, 3, 2, 1, 0, 0, 0, 1, 2, 3, 4, 6, 8, 9, 10, 9, 8, 8],
}
FLAVOURS = {
    "2a03":    {"lead": {"type": "pulse", "duty": .25}, "arp": {"type": "pulse", "duty": .125}, "bass": {"type": "triangle"},
                "pad": {"type": "pulse", "duty": .5}, "counter": {"type": "pulse", "duty": .5}},
    "gameboy": {"lead": {"type": "pulse", "duty": .5}, "arp": {"type": "pulse", "duty": .125}, "bass": {"type": "wave", "table": "bass"},
                "pad": {"type": "wave", "table": "organ"}, "counter": {"type": "pulse", "duty": .25}},
    "sid":     {"lead": {"type": "pulse", "duty": .3, "pwm": .18, "filter": "sweep"}, "arp": {"type": "pulse", "duty": .4, "pwm": .25},
                "bass": {"type": "saw", "filter": "pluck"}, "pad": {"type": "saw", "filter": "soft", "detune": .08},
                "counter": {"type": "triangle", "steps": 0}},
    "fm":      {"lead": {"type": "fm", "ratio": 1, "index": 2.2, "idecay": 3}, "arp": {"type": "fm", "ratio": 3.5, "index": 1.6, "idecay": 9},
                "bass": {"type": "fm", "ratio": .5, "index": 3.0, "idecay": 6}, "pad": {"type": "fm", "ratio": 2, "index": .8, "idecay": .5},
                "counter": {"type": "fm", "ratio": 1, "index": 1.0, "idecay": 2}},
}


def hz(m): return 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)


def adsr(n, a=.004, d=.08, s=.0, r=.03, steps=0):
    t = np.arange(n) / SR; dur = n / SR
    e = np.where(t < a, t / max(a, 1e-5), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    e = e * np.clip((dur - t) / max(r, 1e-4), 0, 1)
    if steps: e = np.round(e * steps) / steps                 # chip volume registers
    return e


def freq_curve(n, midi, v, glide_from=None):
    t = np.arange(n) / SR
    m = np.full(n, float(midi))
    if v.get("sweep"):                                         # semitones over the note (pew / drop / rise)
        m = m + v["sweep"] * np.clip(t / v.get("sweep_time", .12), 0, 1)
    if v.get("arp"):                                           # chip arpeggio (fast chord) e.g. [0,4,7] at 50 Hz
        iv = np.asarray(v["arp"], float); rate = v.get("arp_rate", 50.0)
        m = m + iv[(t * rate).astype(int) % len(iv)]
    if glide_from is not None and v.get("glide"):
        g = v["glide"]; m = m + (glide_from - midi) * np.clip(1 - t / g, 0, 1)
    if v.get("vibrato"):
        dly = v.get("vib_delay", .12)
        m = m + v["vibrato"] * np.sin(2 * math.pi * v.get("vib_rate", 5.5) * t) * np.clip((t - dly) / .1, 0, 1)
    return hz(m)


def _onepole(x, a):
    try:
        from scipy.signal import lfilter
        return lfilter([a], [1, a - 1], x)
    except ImportError:
        y = np.empty_like(x); acc = 0.0
        for i, s in enumerate(x): acc += a * (s - acc); y[i] = acc
        return y


def osc(v, f):
    """Oscillator for voice dict v and per-sample frequency f -> float array in [-1,1]."""
    typ = v.get("type", "pulse"); n = len(f)
    ph = np.cumsum(f) / SR
    if typ == "pulse":
        duty = v.get("duty", .25)
        if v.get("pwm"):
            t = np.arange(n) / SR; duty = np.clip(duty + v["pwm"] * np.sin(2 * math.pi * v.get("pwm_rate", 3.0) * t), .05, .95)
        y = np.where((ph % 1.0) < duty, 1.0, -1.0)
        if v.get("detune"):
            ph2 = np.cumsum(f * (1 + v["detune"] / 100)) / SR; y = .6 * y + .4 * np.where((ph2 % 1.0) < duty, 1.0, -1.0)
        return y * .5
    if typ == "triangle":
        tri = 1 - 4 * np.abs((ph % 1.0) - .5); st = v.get("steps", 7.5)
        return (np.round(tri * st) / st if st else tri)
    if typ == "saw":
        y = 2 * (ph % 1.0) - 1
        if v.get("detune"):
            y = .6 * y + .4 * (2 * ((np.cumsum(f * (1 + v["detune"] / 100)) / SR) % 1.0) - 1)
        return y * .6
    if typ == "wave":
        tb = v.get("table", "bass"); tb = np.asarray(WAVETABLES[tb] if isinstance(tb, str) else tb, float)
        return (tb[((ph % 1.0) * 32).astype(int) % 32] / 7.5 - 1) * .8
    if typ == "fm":
        t = np.arange(n) / SR
        idx = v.get("index", 2.0) * np.exp(-t * v.get("idecay", 3.0))
        mod = np.sin(2 * math.pi * np.cumsum(f * v.get("ratio", 1.0)) / SR)
        return np.sin(2 * math.pi * ph + idx * mod) * .8
    if typ == "noise":
        per = max(1, int(v.get("period", 1)))
        r = np.random.default_rng(v.get("_seed", 0)); vals = r.choice([-1.0, 1.0], n // per + 2)
        if v.get("short"): vals = np.tile(vals[:93], len(vals) // 93 + 1)[:len(vals)]   # 93-step metallic LFSR
        return np.repeat(vals, per)[:n] * .5
    if typ == "math":
        # math voice: the function f(t) is evaluated directly per sample.
        # v["math_fn"] is a callable taking (t_seconds) -> y in [-1, 1] (or any range, scaled).
        # v["math_scale"] maps y → frequency multiplier or direct frequency.
        # v["math_mode"] = "freq" (y → frequency multiplier around base midi) or "amp" (y → amplitude) or "direct" (y → waveform).
        fn = v.get("math_fn")
        mode = v.get("math_mode", "freq")  # "freq" | "amp" | "direct"
        scale = float(v.get("math_scale", 1.0))
        if fn is None:
            return np.zeros(n)
        t = np.arange(n) / SR
        y = np.zeros(n)
        for i, ti in enumerate(t):
            try:
                y[i] = float(fn(ti))
            except Exception:
                y[i] = 0.0
        if mode == "amp":
            return y * scale
        elif mode == "freq":
            # y in [-1,1] → frequency multiplier around base frequency
            # base frequency comes from midi param in note()
            return None  # handled in note() by modulating frequency
        elif mode == "direct":
            # y is the waveform itself (must be [-1,1])
            return y * scale
    raise ValueError(f"unknown voice type {typ}")


def note(v, midi, dur, glide_from=None, flavour="2a03"):
    """Render one note (seconds) for voice v."""
    n = max(1, int(dur * SR))
    typ = v.get("type", "pulse")
    if typ == "math":
        # math voice: evaluate the math function per sample, use it to modulate frequency or amplitude
        fn = v.get("math_fn")
        mode = v.get("math_mode", "freq")  # "freq" | "amp" | "direct"
        scale = float(v.get("math_scale", 1.0))
        base_freq = float(v["math_carrier_hz"]) if v.get("math_carrier_hz") else hz(midi)
        t = np.arange(n) / SR
        y_vals = np.zeros(n)
        for i, ti in enumerate(t):
            try:
                y_vals[i] = float(fn(ti))
            except Exception:
                y_vals[i] = 0.0
        if mode == "amp":
            # y directly modulates amplitude
            y = y_vals * scale
        elif mode == "direct":
            # y is the waveform
            y = y_vals * scale
        else:
            # "freq" mode: y modulates frequency around base
            # y in [-1,1] → frequency multiplier (1 + scale * y)
            ph = np.cumsum(base_freq * (1.0 + scale * y_vals)) / SR
            waveform = v.get("math_waveform", "sine")  # sine, pulse, triangle
            if waveform == "pulse":
                duty = v.get("duty", .25)
                y = np.where((ph % 1.0) < duty, 1.0, -1.0) * .5
            elif waveform == "triangle":
                tri = 1 - 4 * np.abs((ph % 1.0) - .5)
                st = v.get("steps", 7.5)
                y = (np.round(tri * st) / st if st else tri)
            else:  # sine
                y = np.sin(2 * math.pi * ph)
            y = y * scale
    else:
        f = freq_curve(n, midi, v, glide_from)
        y = osc(v, f)
    e = v.get("env", {})
    env = adsr(n, e.get("a", .004), e.get("d", .09), e.get("s", .35), e.get("r", .03),
               steps=(15 if flavour in ("2a03", "gameboy") else 0))
    y = y * env
    flt = v.get("filter")
    if flt:
        t = np.arange(n) / SR
        if flt == "sweep": fc = 600 + 5000 * np.exp(-t * 4)
        elif flt == "pluck": fc = 300 + 2500 * np.exp(-t * 14)
        elif flt == "soft": fc = np.full(n, 1400.0)
        else: fc = np.full(n, float(flt))
        a = np.clip(2 * np.pi * fc / SR, .001, .99)
        y = _onepole(y, float(a.mean())) * 1.6 if n > SR // 2 else _onepole(y, float(a[: max(1, n // 4)].mean())) * 1.6
    if flavour == "gameboy": y = np.round(y * 7) / 7
    return y


def voice_cfg(name, user, flavour):
    """Merge flavour defaults for the voice's role with the user's settings."""
    role = user.get("role", name)
    base = dict(FLAVOURS.get(flavour, FLAVOURS["2a03"]).get(role, {"type": "pulse", "duty": .25}))
    base.update(user); base.setdefault("role", role)
    return base
