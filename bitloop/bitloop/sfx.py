"""Chip SFX palette. Every visual event and transition maps to one of these (remappable per spec via music.sfx)."""
import math
import numpy as np
from .voices import SR, adsr, hz
from .drums import _noise


def _lp(x, a):
    from scipy.signal import lfilter
    return lfilter([a], [1, a - 1], x)


def _sq(f, n, duty=.5):
    ph = np.cumsum(np.broadcast_to(f, (n,))) / SR
    return np.where(ph % 1 < duty, 1.0, -1.0) * .5


def render(kind, root, B):
    """-> list of (offset_seconds, signal, vol, pan). B = beat length at the event (s); root = key root MIDI (bass octave)."""
    t_ = lambda d: np.arange(int(d * SR)) / SR
    if kind in ("hit", "boom", "drop"):
        big = kind != "hit"; t = t_(1.8 if big else 1.4)
        cr = _lp(_noise(len(t), 99), .7) * np.exp(-t * (2.2 if big else 2.8))
        k = np.sin(2 * math.pi * np.cumsum(38 + 170 * np.exp(-t * 28)) / SR) * np.exp(-t * (5 if big else 7))
        b = 1 - 4 * np.abs(((np.arange(len(t)) * hz(root) / SR) % 1) - .5); b = np.round(b * 7.5) / 7.5 * np.exp(-t * 2)
        return [(0, cr, .22, 0), (0, k, .75 if big else .65, 0), (0, b, .3, 0)]
    if kind == "riser":
        d = 2 * B; t = t_(d); f = 200 * (8 ** (t / d))
        return [(-d, _sq(f, len(t)) * (t / d) ** 2, .06, -.2), (-d, _lp(_noise(len(t), 5), .3) * (t / d) ** 2, .12, .2)]
    if kind in ("whoosh", "swipe"):
        d = (1.0 if kind == "whoosh" else .5) * B; t = t_(d); e = np.sin(np.pi * t / d) ** 2
        a = np.clip(.05 + .5 * e, .01, .9)
        return [(-d / 2, _lp(_noise(len(t), 11), .25 if kind == "whoosh" else .45) * e, .22, -.3 if kind == "swipe" else 0)]
    if kind == "shimmer":
        out = []
        for i in range(12):
            d = B / 8; f = hz(root + 48 + [0, 7, 12, 16, 19, 24][i % 6]); n = int(d * SR)
            out.append((i * B / 8, _sq(f, n, .125) * adsr(n, .002, .04), .05 * (1 - i / 14), .4 * ((-1) ** i)))
        return out
    if kind == "zap":
        t = t_(.16); f = 2200 * np.exp(-t * 18) + 120
        return [(-.3 * B, _sq(f, len(t)) * np.exp(-t * 12), .1, 0)]
    if kind == "tick":
        n = int(.035 * SR); return [(0, _sq(hz(root + 60), n, .25) * adsr(n, .001, .012), .035, .2)]
    if kind.startswith("blip"):        # narration typewriter blip: soft, short, low in the mix ("blip_hi" on vowels)
        base, _, v = kind.partition("@"); g = float(v) if v else 1.0
        n = int(.028 * SR); f = hz(root + (55 if base == "blip_hi" else 50))
        sig = _lp(_sq(f, n, .25), .35) * adsr(n, .001, .018)
        return [(0, sig, .028 * g, .15 if base == "blip_hi" else -.15)]
    if kind == "pop":
        t = t_(.09); f = hz(root + 48) * (1 + 2 * np.exp(-t * 60))
        return [(0, _sq(f, len(t), .25) * np.exp(-t * 30), .08, 0)]
    if kind == "thud":
        t = t_(.25); return [(0, np.sin(2 * math.pi * np.cumsum(60 + 60 * np.exp(-t * 30)) / SR) * np.exp(-t * 14), .4, 0)]
    if kind == "glitch":
        out = []; r = np.random.default_rng(int(root * 7))
        for i in range(6):
            d = .03 + .03 * r.random(); n = int(d * SR)
            sig = _sq(hz(root + 36 + r.integers(0, 36)), n, .5) if i % 2 else _noise(n, i, 6) * .6
            out.append((i * .045 - .12, sig * adsr(n, .001, .03), .09, (-1) ** i * .5))
        return out
    if kind == "bitcrush":   # mosaic burst: descending stepped pitch
        d = .5 * B; t = t_(d); f = hz(root + 60 - 24 * np.floor(t / d * 8) / 8)
        return [(-d / 2, _sq(f, len(t), .125) * np.sin(np.pi * t / d), .07, 0)]
    if kind == "tiles":      # çini wipe: quick rising arpeggio ticks
        out = []
        for i in range(8):
            n = int(.03 * SR); out.append((i * B / 8 - B / 4, _sq(hz(root + 48 + [0, 4, 7, 12, 7, 12, 16, 19][i]), n, .25) * adsr(n, .001, .015), .05, .3 * ((-1) ** i)))
        return out
    if kind == "portal":
        d = 1.0 * B; t = t_(d); f = hz(root + 60) * (.25 ** (t / d))
        return [(-d / 2, _sq(f, len(t), .25) * np.sin(np.pi * t / d), .07, 0)] + render("thud", root, B)
    if kind in ("crt_off", "crt_on"):
        d = .35; t = t_(d); f = (3000 * np.exp(-t * 9) + 60) if kind == "crt_off" else (60 + 2800 * (t / d) ** 2)
        return [(-d / 2 if kind == "crt_off" else 0, _sq(f, len(t), .5) * np.sin(np.pi * t / d), .05, 0),
                (0, _lp(_noise(len(t), 13), .5) * np.exp(-t * 8), .05, 0)]
    if kind == "crt":
        return render("crt_off", root, B) + [(o + .5 * B, sg, v, pn) for o, sg, v, pn in render("crt_on", root, B)]
    if kind == "spin":
        d = .75 * B; t = t_(d); f = hz(root + 36) * (2 ** (2 * t / d))
        return [(-d / 2, _sq(f, len(t), .25) * np.sin(np.pi * t / d) * (1 + .5 * np.sin(2 * math.pi * 16 * t)), .05, 0)]
    if kind == "flash":
        t = t_(.4); return [(0, _lp(_noise(len(t), 21), .8) * np.exp(-t * 10), .12, 0)] + render("pop", root, B)
    if kind == "crash":
        t = t_(1.4); return [(0, _noise(len(t), 9) * np.exp(-t * 2.8) * .6, .2, 0)]
    if kind == "split":
        return render("swipe", root, B) + render("tick", root, B)
    return []


def mix(mix_obj, t, kind, root, B):
    for off, sig, vol, pan in render(kind, root, B):
        mix_obj.add(t + off, sig, vol, pan)
