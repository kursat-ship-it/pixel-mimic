"""Drum patterns (16th-note step grids, one string per instrument per bar) + chip drum kit.
Step chars: X accent, x hit, o ghost, r roll (two 32nds), . rest.
Instruments: K kick, S snare, C clap, H closed hat, O open hat, D düm (low darbuka/tom), T tek (high click),
M tom, R rim, Z crash, B bat chirp (FM down-sweep 4→1.5 kHz, 18 ms; the sonar vision rings fire on its hits).
A grid whose length is a multiple of the bar's steps is a MULTI-BAR grid: bar k of the section plays slice k (cycling).
Keys starting with "_" are comments. Any meter: if a pattern's length ≠ steps per bar it is tiled/cropped; "auto" builds a
groove from the meter's grouping (aksak meters accent their 2+2+3 groups)."""
import math
import numpy as np
from .voices import SR, adsr

PATTERNS = {
    "none": {},
    "four_on_floor": {"meter": "4/4", "K": "X...x...X...x...", "C": "....X.......X...", "H": "..x...x...x...x.", "O": "..............x."},
    "breakbeat": {"meter": "4/4", "K": "X.x.......xx....", "S": "....X..o.o..X..o", "H": "x.x.x.x.x.x.x.x."},
    "trap": {"meter": "4/4", "K": "X......x..x.....", "S": "........X.......", "H": "x.x.x.x.x.rrx.xr", "O": "..............x."},
    "half_time": {"meter": "4/4", "K": "X.....x.........", "S": "........X.......", "H": "x...x...x...x..o"},
    "boom_bap": {"meter": "4/4", "K": "X......x.xx.....", "S": "....X.......X...", "H": "x.x.x.x.x.x.x.xo"},
    "maqsum": {"meter": "4/4", "D": "X.......X.......", "T": "..x...x.....x...", "H": "....o.......o..."},
    "aksak_9_8": {"meter": "9/8", "D": "X.......X.........", "T": "....x.......x.x...", "H": "x.x.x.x.x.x.x.x.x.", "K": "X................."},
    "aksak_7_8": {"meter": "7/8", "D": "X.......X.....", "T": "....x.......x.", "H": "x.x.x.x.x.x.x.", "K": "X..........x.."},
    "waltz": {"meter": "3/4", "K": "X...........", "S": "....o...o...", "H": "..x...x...x.", "D": "X..........."},
    "six_eight": {"meter": "6/8", "K": "X.....x.....", "S": "......X.....", "H": "x.x.x.x.x.x."},
    "shuffle": {"meter": "4/4", "swing": .8, "K": "X.....x.X.......", "S": "....X.......X..o", "H": "x.x.x.x.x.x.x.x."},
    "march": {"meter": "4/4", "K": "X.......X.......", "S": "....x.xx....x.rr", "H": "x...x...x...x..."},
    "dnb": {"meter": "4/4", "K": "X.........X.....", "S": "....X.......X...", "H": "x.x.x.x.x.x.x.x."},
}
MIN_ENERGY = {"B": 1.0, "K": 1.0, "D": .8, "T": 1.0, "H": 1.5, "S": 1.5, "C": 1.8, "O": 2.5, "M": 2.0, "R": 1.2, "Z": 9}
VOL = {"B": .12, "K": .55, "S": .18, "C": .16, "H": .05, "O": .06, "D": .48, "T": .14, "M": .3, "R": .1, "Z": .2}


def auto_pattern(meter):
    n = meter.steps; K, S, H, T = ["."] * n, ["."] * n, ["."] * n, ["."] * n
    starts = [int(round(g * 4)) for g in meter.group_starts]
    pulse = int(round(meter.unit * 4)); eighth = 2
    for i in range(0, n, min(pulse, eighth) if meter.den == 8 else eighth): H[i] = "x"
    K[0] = "X"
    for j, st in enumerate(starts[1:], 1):
        (S if j == len(starts) - 1 else T)[st] = "X" if j == len(starts) - 1 else "x"
        if len(starts) >= 4 and j == len(starts) // 2: K[st] = "x"
    return {"meter": meter.sig, "K": "".join(K), "S": "".join(S), "H": "".join(H), "T": "".join(T)}


def resolve(name_or_grid, meter):
    if isinstance(name_or_grid, dict): p = dict(name_or_grid)
    elif name_or_grid in (None, "auto"): p = auto_pattern(meter)
    else:
        if name_or_grid not in PATTERNS: raise ValueError(f"unknown drum pattern '{name_or_grid}' — {', '.join(PATTERNS)}, auto, or a grid")
        p = dict(PATTERNS[name_or_grid])
        if p.get("meter") and p["meter"] != meter.sig and name_or_grid != "none":
            p = {**auto_pattern(meter), "swing": p.get("swing", 0)}     # wrong meter → derive from the meter instead
    return p


PAN = {"H": .3, "O": .3, "T": .25, "B": -.2}


def hits_in_bar(p, meter, energy, fill=False, bar=0):
    """-> [(beat_offset, inst, vel)] for one bar (bar = index inside the section, selects the slice of a multi-bar grid)."""
    out = []; n = meter.steps
    for inst, grid in p.items():
        if inst in ("meter", "swing") or inst.startswith("_") or not isinstance(grid, str): continue
        if energy < MIN_ENERGY.get(inst, 1.0): continue
        off = (bar % (len(grid) // n)) * n if len(grid) >= 2 * n and len(grid) % n == 0 else 0
        for i in range(n):
            c = grid[(off + i) % len(grid)]
            if c == ".": continue
            b = i * .25
            if p.get("swing") and i % 4 == 2: b += p["swing"] / 6
            vel = {"X": 1.0, "x": .8, "o": .4, "r": .7}[c] if c in "Xxor" else .8
            out.append((b, inst, vel))
            if c == "r": out.append((b + .125, inst, .55))
    if fill:  # snare/tom roll over the last group, crescendo
        g0 = meter.group_starts[-1] if len(meter.group_starts) > 1 else meter.bar_beats - 1
        k = 0; b = g0
        while b < meter.bar_beats - 1e-6:
            out.append((b, "S" if k % 2 == 0 else "M", .45 + .5 * (b - g0) / max(meter.bar_beats - g0, .1))); b += .25; k += 1
    return out


def _noise(n, seed, period=1):
    r = np.random.default_rng(seed); v = r.choice([-1.0, 1.0], n // period + 2)
    return np.repeat(v, period)[:n]


def drum(inst, flavour="2a03", seed=0):
    """One drum hit as float array."""
    def t_(d): return np.arange(int(d * SR)) / SR
    if inst == "K":
        t = t_(.2); f = 45 + 120 * np.exp(-t * 35)
        y = np.sin(2 * math.pi * np.cumsum(f) / SR)
        if flavour == "2a03": y = np.round(y * 7.5) / 7.5
        return y * np.exp(-t * 16)
    if inst in ("S", "C"):
        t = t_(.16 if inst == "S" else .2); nz = _noise(len(t), seed, 2 if flavour == "gameboy" else 1)
        if inst == "C":
            e = sum(np.exp(-np.clip(t - o, 0, None) * 60) * (t >= o) for o in (0, .012, .024)) * np.exp(-t * 9)
            return nz * e * .9
        tone = np.sin(2 * math.pi * 190 * t) * np.exp(-t * 30)
        return (nz * np.exp(-t * 22) * .8 + tone * .5)
    if inst in ("H", "O"):
        d = .03 if inst == "H" else .2; n = int(d * SR)
        nz = np.diff(_noise(n, seed + 3, 1), prepend=0) * .5
        return nz * adsr(n, .001, .008 if inst == "H" else .07, 0, .01)
    if inst in ("D", "M"):
        t = t_(.22); f0 = 70 if inst == "D" else 140
        y = np.sin(2 * math.pi * np.cumsum(f0 + 90 * np.exp(-t * 28)) / SR)
        return np.round(y * 7) / 7 * np.exp(-t * 13)
    if inst in ("T", "R"):
        n = int(.04 * SR); y = np.diff(_noise(n, seed + 5, 2), prepend=0) * adsr(n, .0005, .01, 0, .005)
        if inst == "R": y += np.sin(2 * math.pi * 1700 * np.arange(n) / SR) * adsr(n, .0005, .01, 0, .005) * .4
        return y
    if inst == "B":     # bat chirp: FM down-sweep 4 kHz → 1.5 kHz in 18 ms + a breath of noise
        t = t_(.018); f = 1500 + 2500 * np.exp(-t / .006)
        ph = 2 * math.pi * np.cumsum(f) / SR
        y = np.sin(ph + .8 * np.sin(ph * 2)) * np.sin(math.pi * t / .018) ** .6
        return y * .9 + _noise(len(t), seed + 7, 1) * np.exp(-t * 200) * .12
    if inst == "Z":
        t = t_(1.4); return _noise(len(t), seed + 9, 1) * np.exp(-t * 2.8) * .6
    raise ValueError(inst)
