"""One timeline for picture, music and SFX.

Timeline unit = 1 BEAT = one quarter note, always (DAW convention). `bpm` is quarter notes per minute.
A 7/8 bar is 3.5 beats, a 6/8 bar 3 beats, a 3/4 bar 3 beats. Tempo can change or ramp per music section;
TempoMap converts beats <-> seconds by integrating 60/bpm(beat), so every frame, note and SFX uses the same clock."""
import numpy as np

DEFAULT_GROUPING = {  # pulses of the denominator unit per group (accent structure)
    "2/4": [1, 1], "3/4": [1, 1, 1], "4/4": [1, 1, 1, 1], "5/4": [3, 2], "6/4": [3, 3], "7/4": [4, 3],
    "5/8": [2, 3], "6/8": [3, 3], "7/8": [2, 2, 3], "9/8": [2, 2, 2, 3], "10/8": [3, 2, 2, 3], "11/8": [2, 2, 3, 2, 2],
    "12/8": [3, 3, 3, 3],
}


class Meter:
    def __init__(self, sig="4/4", grouping=None):
        if isinstance(sig, Meter): sig, grouping = sig.sig, grouping or sig.grouping
        self.sig = sig; n, d = sig.split("/"); self.num, self.den = int(n), int(d)
        self.grouping = list(grouping or DEFAULT_GROUPING.get(sig, [1] * self.num))
        if sum(self.grouping) != self.num: raise ValueError(f"grouping {self.grouping} does not sum to {self.num} for {sig}")
        self.unit = 4.0 / self.den                       # beats per denominator pulse
        self.bar_beats = self.num * self.unit
        self.steps = int(round(self.bar_beats * 4))      # 16th-note steps per bar
        g, acc = [], 0
        for k in self.grouping: g.append(acc * self.unit); acc += k
        self.group_starts = g                            # beat offsets of the accented pulses in a bar

    def __repr__(self): return f"Meter({self.sig},{self.grouping})"


class TempoMap:
    """Piecewise-linear tempo (in beats). pieces = [(b0, b1, bpm0, bpm1)], contiguous from 0."""
    RES = 96

    def __init__(self, pieces, total_beats):
        self.pieces = pieces or [(0.0, max(total_beats, 1.0), 120.0, 120.0)]
        self.total = total_beats
        end = max(total_beats, self.pieces[-1][1]) + 8
        self.b = np.arange(0, end + 1.0 / self.RES, 1.0 / self.RES)
        bpm = np.full_like(self.b, self.pieces[-1][3])
        for b0, b1, t0, t1 in self.pieces:
            m = (self.b >= b0) & (self.b < b1)
            bpm[m] = t0 + (t1 - t0) * (self.b[m] - b0) / max(b1 - b0, 1e-9)
        self.bpm = bpm
        spb = 60.0 / bpm
        dt = .5 * (spb[:-1] + spb[1:]) / self.RES                 # trapezoid rule: exact for constant tempo, ~µs on ramps
        self.t = np.concatenate([[0.0], np.cumsum(dt)])
        self.bpm0 = self.pieces[0][2]

    def time(self, beat):
        beat = np.asarray(beat, float)
        out = np.interp(beat, self.b, self.t)
        out = np.where(beat < 0, beat * 60.0 / self.bpm0, out)
        over = beat > self.b[-1]
        return float(out) if out.ndim == 0 else out if not over.any() else np.where(over, self.t[-1] + (beat - self.b[-1]) * 60 / self.bpm[-1], out)

    def beat(self, t):
        t = np.asarray(t, float)
        out = np.interp(t, self.t, self.b)
        out = np.where(t < 0, t * self.bpm0 / 60.0, out)
        return float(out) if out.ndim == 0 else out

    def bpm_at(self, beat): return float(np.interp(beat, self.b, self.bpm))

    def beat_len(self, beat): return 60.0 / self.bpm_at(beat)


_CACHE = {}


def tempo_map(spec):
    """TempoMap for a normalised spec (cached; rebuilt from the JSON-safe spec['_tempo'] so workers can use it)."""
    key = (id(spec), json_key(spec))
    tm = _CACHE.get(key)
    if tm is None:
        tm = TempoMap([tuple(p) for p in spec["_tempo"]], spec["total_beats"]); _CACHE.clear(); _CACHE[key] = tm
    return tm


def json_key(spec): return (tuple(tuple(p) for p in spec["_tempo"]), spec["total_beats"])
