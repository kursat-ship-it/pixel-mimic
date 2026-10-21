"""Scales / makams, chords, progressions, motifs. Pitches are float MIDI numbers so microtonal makam
approximations work (tuning "approx"); default tuning is 12-TET."""
import re
import numpy as np

NOTE = {"C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3, "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
        "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11}

# name: (12-TET semitones, approximate cents or None, short description)
SCALES = {
    "major":            ([0, 2, 4, 5, 7, 9, 11], None, "bright, resolved"),
    "minor":            ([0, 2, 3, 5, 7, 8, 10], None, "natural minor, serious"),
    "dorian":           ([0, 2, 3, 5, 7, 9, 10], None, "minor but hopeful (raised 6th)"),
    "phrygian":         ([0, 1, 3, 5, 7, 8, 10], None, "dark, tense ♭2"),
    "lydian":           ([0, 2, 4, 6, 7, 9, 11], None, "floating, wonder (♯4)"),
    "mixolydian":       ([0, 2, 4, 5, 7, 9, 10], None, "rock/heroic major (♭7)"),
    "locrian":          ([0, 1, 3, 5, 6, 8, 10], None, "unstable, eerie"),
    "harmonic_minor":   ([0, 2, 3, 5, 7, 8, 11], None, "dramatic, classical"),
    "melodic_minor":    ([0, 2, 3, 5, 7, 9, 11], None, "jazzy, ascending minor"),
    "phrygian_dominant": ([0, 1, 4, 5, 7, 8, 10], None, "= Hicaz in 12-TET"),
    "pentatonic_major": ([0, 2, 4, 7, 9], None, "open, playful, can't go wrong"),
    "pentatonic_minor": ([0, 3, 5, 7, 10], None, "groovy, bluesy"),
    "blues":            ([0, 3, 5, 6, 7, 10], None, "blue note ♭5"),
    "whole_tone":       ([0, 2, 4, 6, 8, 10], None, "dreamlike, weightless, sci-fi"),
    "chromatic":        (list(range(12)), None, "everything"),
    "hirajoshi":        ([0, 2, 3, 7, 8], None, "Japanese pentatonic, mysterious"),
    # Turkish makams — 12-TET approximation + an approximate microtonal version (cents, simplified AEU-style)
    "hicaz":   ([0, 1, 4, 5, 7, 8, 10], [0, 114, 384, 498, 702, 792, 996], "augmented 2nd = 'hayret'"),
    "ussak":   ([0, 1, 3, 5, 7, 8, 10], [0, 150, 294, 498, 702, 792, 996], "Uşşak: segah 2nd, warm melancholy"),
    "kurdi":   ([0, 1, 3, 5, 7, 8, 10], [0, 90, 294, 498, 702, 792, 996], "Kürdi: plain ♭2, sober"),
    "nihavend": ([0, 2, 3, 5, 7, 8, 11], [0, 204, 294, 498, 702, 792, 1088], "Nihavend: minor with leading tone"),
    "rast":    ([0, 2, 4, 5, 7, 9, 11], [0, 204, 355, 498, 702, 906, 1059], "Rast: major with lowered 3rd/7th"),
    "huzzam":  ([0, 1, 3, 4, 7, 8, 10], [0, 150, 350, 465, 760, 850, 1050], "Hüzzam: segah tonic + hicaz colour (rough approx.)"),
    "saba":    ([0, 2, 3, 4, 7, 8, 10], [0, 150, 294, 384, 702, 792, 996], "Saba: grieving, diminished 4th"),
}
ALIASES = {"uşşak": "ussak", "kürdi": "kurdi", "hüzzam": "huzzam", "aeolian": "minor", "ionian": "major",
           "harmonic minor": "harmonic_minor", "whole-tone": "whole_tone", "pentatonic": "pentatonic_major",
           "major_pentatonic": "pentatonic_major", "minor_pentatonic": "pentatonic_minor", "melodic minor": "melodic_minor"}
ROMAN = {"I": 0, "II": 1, "III": 2, "IV": 3, "V": 4, "VI": 5, "VII": 6}


def scale_name(n):
    n = (n or "minor").lower(); n = ALIASES.get(n, n)
    if n not in SCALES: raise ValueError(f"unknown scale '{n}' — known: {', '.join(SCALES)}")
    return n


class Scale:
    def __init__(self, key="D", name="minor", tuning="12tet"):
        self.name = scale_name(name); semis, cents, _ = SCALES[self.name]
        self.key = key; self.root = NOTE[key.upper()] if isinstance(key, str) else int(key) % 12
        self.steps = [c / 100.0 for c in cents] if (tuning == "approx" and cents) else [float(s) for s in semis]
        self.n = len(self.steps)

    def degree(self, d, octave=4):
        """Scale degree d (0-based, any int) -> float MIDI; octave 4 = tonic in C4 octave."""
        o, k = divmod(int(d), self.n)
        return 12 * (octave + 1 + o) + self.root + self.steps[k]

    def snap(self, midi):
        """Nearest scale pitch."""
        base = 12 * np.floor((midi - self.root) / 12) + self.root
        c = [base + s + 12 * o for o in (-1, 0, 1) for s in self.steps]
        return min(c, key=lambda x: abs(x - midi))

    def fifth_index(self):
        return min(range(self.n), key=lambda k: abs(self.steps[k] - 7))


def parse_note(s):
    m = re.match(r"^([A-Ga-g][#b]?)(-?\d)$", s.strip())
    if not m: raise ValueError(f"bad note '{s}' (use e.g. E3, Bb4, F#2)")
    return 12 * (int(m.group(2)) + 1) + NOTE[m.group(1).upper()]


CHORD_Q = {"": [0, 4, 7], "m": [0, 3, 7], "dim": [0, 3, 6], "aug": [0, 4, 8], "sus2": [0, 2, 7], "sus4": [0, 5, 7],
           "7": [0, 4, 7, 10], "m7": [0, 3, 7, 10], "maj7": [0, 4, 7, 11], "m7b5": [0, 3, 6, 10], "dim7": [0, 3, 6, 9],
           "add9": [0, 4, 7, 14], "m9": [0, 3, 7, 10, 14], "5": [0, 7, 12]}


def chord(sym, sc, octave=3):
    """Chord -> list of float MIDI around `octave`.
    Roman: 'i', 'IV', 'bVI', 'V7', 'viio', 'II+' — plain numerals are DIATONIC to the scale (stacked scale tones, so
    they work for makams/pentatonics too); an accidental (b/#) or a suffix (7, o, +, sus4, maj7) forces the quality
    from the case (UPPER = major, lower = minor). Explicit: 'Em', 'C#m7', 'Fmaj7', 'Gsus4' or ['E3','G3','B3']."""
    if isinstance(sym, (list, tuple)): return [float(parse_note(n)) if isinstance(n, str) else float(n) for n in sym]
    s = sym.strip()
    m = re.match(r"^([b#]?)(VII|VI|V|IV|III|II|I|vii|vi|v|iv|iii|ii|i)(o|\+|°|ø)?(maj7|m7|sus2|sus4|7|9|add9)?$", s)
    if m:
        acc, num, q, ext = m.groups(); d = ROMAN[num.upper()] % sc.n if sc.n >= 7 else ROMAN[num.upper()]
        if not acc and not q and not ext:
            return [sc.degree(d + 2 * k, octave) for k in range(3)]
        base = sc.degree(d, octave)
        if sc.n < 7: base = sc.degree(0, octave) + [0, 2, 4, 5, 7, 9, 11][ROMAN[num.upper()]]
        base += {"b": -1, "#": 1, "": 0}[acc]
        if acc:  # accidental numerals are relative to the major scale of the key (bVI = minor 6th above tonic)
            base = sc.degree(0, octave) + [0, 2, 4, 5, 7, 9, 11][ROMAN[num.upper()]] + {"b": -1, "#": 1}[acc]
        minor = num.islower()
        iv = [0, 3, 7] if minor else [0, 4, 7]
        if q in ("o", "°"): iv = [0, 3, 6]
        if q == "+": iv = [0, 4, 8]
        if q == "ø": iv = [0, 3, 6, 10]
        if ext == "7": iv = iv + ([10] if q not in ("o", "°") else [9])
        elif ext == "maj7": iv = iv + [11]
        elif ext == "m7": iv = [0, 3, 7, 10]
        elif ext in ("sus2", "sus4"): iv = CHORD_Q[ext]
        elif ext in ("9", "add9"): iv = iv + [14]
        return [base + i for i in iv]
    m = re.match(r"^([A-G][#b]?)(.*)$", s)
    if m and m.group(2) in CHORD_Q:
        r = NOTE[m.group(1).upper()]; base = 12 * (octave + 1) + r
        return [float(base + i) for i in CHORD_Q[m.group(2)]]
    raise ValueError(f"cannot parse chord '{sym}'")


CONTOURS = {
    "arch": lambda x: np.sin(np.pi * x), "rise": lambda x: x, "fall": lambda x: 1 - x,
    "wave": lambda x: .5 + .5 * np.sin(2 * np.pi * x), "valley": lambda x: 1 - np.sin(np.pi * x),
    "zigzag": lambda x: np.abs(((x * 4) % 2) - 1), "question": lambda x: np.where(x < .75, .3 + .2 * np.sin(6 * x), .3 + 2.8 * (x - .75)),
    "flat": lambda x: x * 0 + .4,
}


def motif(spec_m, meter, rng, bars=2):
    """Melodic motif -> list of (beat_offset, dur_beats, degree or None), spanning `bars` bars of `meter`.
    spec_m: {"notes": [0,2,null,4...], "rhythm": [0.5,...]} explicit, or {"contour": "arch", "range": 7,
    "density": 0.65, "seed": 3} generated (accents on group starts, ends on a chord tone)."""
    spec_m = spec_m or {}
    if spec_m.get("notes"):
        notes = spec_m["notes"]; rh = spec_m.get("rhythm") or [meter.unit / 2 if meter.den == 8 else .5]
        out, b = [], 0.0
        for i, n in enumerate(notes):
            d = rh[i % len(rh)]; out.append((b, d, n)); b += d
        return out, b
    r = np.random.default_rng(spec_m.get("seed", int(rng.integers(1 << 30))))
    step = .5                                    # eighth-note grid
    total = meter.bar_beats * bars; n = int(round(total / step))
    accents = set()
    for bar in range(bars):
        for g in meter.group_starts: accents.add(round((bar * meter.bar_beats + g) / step))
    dens = spec_m.get("density", .62); rng_ = spec_m.get("range", 7)
    cf = CONTOURS.get(spec_m.get("contour", "arch"), CONTOURS["arch"])
    out, i = [], 0
    while i < n:
        on = i in accents or r.random() < dens * (0.8 if i % 2 else 1.0)
        if i == 0: on = True
        if not on: i += 1; continue
        x = i / max(n - 1, 1); target = float(cf(x)) * rng_
        deg = int(round(target + r.normal(0, .7)))
        if i in accents and r.random() < .6: deg = int(round(deg / 2)) * 2     # strong beats lean to chord tones
        ln = 1
        while i + ln < n and ln < 4 and (i + ln) not in accents and r.random() < .35: ln += 1
        out.append((i * step, ln * step * .95, deg)); i += ln
    if out:  # cadence: land on a chord tone, held
        b, d, _ = out[-1]; out[-1] = (b, max(d, step * 1.9) if b + step * 2 <= total else d, int(spec_m.get("cadence", 0)))
    return out, total


# ------------------------------------------------------------------ integer series (self-similar melodies)
_NORGARD = [0]


def norgard(n):
    """Per Nørgård's infinity series (1959): a(0)=0, a(2n)=-a(n), a(2n+1)=a(n)+1 → 0 1 -1 2 1 0 -2 3 -1 2 0 1 2 -1 -3 4 …
    Self-similar: a(4n)=a(n) (every 4th term is the series itself), a(2n)=-a(n) (every 2nd = its inversion).
    Accepts an int or an int array (negative indices are not defined: wrap them yourself)."""
    arr = np.asarray(n)
    m = int(arr.max()) if arr.size else 0
    while len(_NORGARD) <= m:
        i = len(_NORGARD); _NORGARD.append(-_NORGARD[i // 2] if i % 2 == 0 else _NORGARD[i // 2] + 1)
    if arr.ndim == 0: return _NORGARD[int(arr)]
    return np.asarray(_NORGARD, dtype=int)[arr.astype(int)]


SERIES = {"norgard": norgard}


def list_series(values, period=None):
    """A finite melody as a periodic integer series: value(i) = values[i % period] (period defaults to len(values);
    a shorter period loops only the first `period` values). Accepts an int or an int array, like norgard()."""
    vals = np.asarray([int(v) for v in values], dtype=int); P = int(period or len(vals))
    if not 0 < P <= len(vals): raise ValueError(f"series period {P} must be in 1..{len(vals)}")
    def f(n):
        arr = np.asarray(n)
        out = vals[np.mod(arr.astype(int), P)]
        return int(out) if arr.ndim == 0 else out
    f.values, f.period = vals[:P].tolist(), P
    return f


BUILTIN_SERIES = dict(SERIES)


def register_series(defs):
    """music.series_defs {name: {values:[ints], period:N}} → SERIES (shared by music and visuals). Built-ins are kept;
    previously registered list series are replaced, so loading another spec never leaks melodies."""
    for k in [k for k in SERIES if k not in BUILTIN_SERIES]: del SERIES[k]
    for name, d in (defs or {}).items():
        d = {"values": d} if isinstance(d, list) else d
        SERIES[name] = list_series(d["values"], d.get("period"))


def series_value(name, idx):
    """Named integer series → value(s). idx int or int array (≥ 0)."""
    if name not in SERIES: raise ValueError(f"unknown series '{name}' — {', '.join(SERIES)}")
    return SERIES[name](idx)


def series_index(beat, rate, period=None):
    """Index of the series note sounding at global `beat` for a voice playing `rate` notes per beat
    (floor(beat*rate), wrapped into [0, period) when a loop period is given). Shared by music AND visuals."""
    i = np.floor(np.asarray(beat, float) * rate + 1e-9).astype(int)
    if period: i = np.mod(i, int(period))
    return i if i.ndim else int(i)
