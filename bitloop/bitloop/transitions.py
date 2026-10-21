"""Beat-synced transition library (art-resolution, palette-safe). Each transition blends the outgoing frame `a`
and the incoming frame `b` (uint8 H×W×3, both rendered live) with progress k∈[0,1].

align: where the window sits relative to the cut beat B
  center → [B-d/2, B+d/2] (the visual switch lands ON the beat)   start → [B, B+d]   end → [B-d, B]
Each transition fires a matching SFX at B (see sfx.py), remappable via music.sfx."""
import math
import numpy as np
from .palette import BAYER4

TRANSITIONS = {
    #  name          default beats, align,   sfx         what it looks like
    "cut":        dict(beats=0,    align="start",  sfx=None,      desc="hard cut on the beat"),
    "crash":      dict(beats=1.2,  align="end",    sfx="zap",     desc="camera dives into the outgoing scene's bright focus, cut"),
    "dissolve":   dict(beats=1.5,  align="start",  sfx="shimmer", desc="radial ordered-dither dissolve"),
    "whip":       dict(beats=.5,   align="center", sfx="whoosh",  desc="whip pan with motion smear (dir)"),
    "slide":      dict(beats=.75,  align="center", sfx="swipe",   desc="new scene slides over the old (dir)"),
    "push":       dict(beats=.75,  align="center", sfx="swipe",   desc="new scene pushes the old out (dir)"),
    "mosaic":     dict(beats=.75,  align="center", sfx="bitcrush", desc="pixelate burst up, switch, resolve"),
    "iris":       dict(beats=1.0,  align="start",  sfx="shimmer", desc="hayret-eye shaped iris opens on the new scene"),
    "tiles":      dict(beats=1.0,  align="center", sfx="tiles",   desc="Çini wipe: 8-point star tiles flip diagonally"),
    "glitch":     dict(beats=.5,   align="center", sfx="glitch",  desc="scanline tear + channel split"),
    "match":      dict(beats=.75,  align="start",  sfx="thud",    desc="match cut on shape: new focus starts where the old one was"),
    "silhouette": dict(beats=1.5,  align="center", sfx="shimmer", desc="morph through a shared glowing silhouette (shape, size)"),
    "flash":      dict(beats=.5,   align="center", sfx="flash",   desc="white-hot flash cut"),
    "spin":       dict(beats=1.0,  align="center", sfx="spin",    desc="old spins away, new spins in (over:true = old spins away on top of the new, no black gap)"),
    "split":      dict(beats=2.0,  align="start",  sfx="split",   desc="split screen (old top / new bottom), then new takes over"),
    "portal":     dict(beats=1.25, align="center", sfx="portal",  desc="zoom through the outgoing focus into the new scene"),
    "crt":        dict(beats=1.0,  align="center", sfx="crt",      desc="CRT power-off to a line/dot, power-on into new; floor=0..1 keeps a dim after-image"),
}
ALIASES = {"morph": "dissolve", "shape_morph": "silhouette", "morph_dither": "dissolve", "wipe": "tiles", "eye": "iris", "pixelate": "mosaic", "zoom_through": "portal"}


def ease(k):  # inOutCubic
    return 4 * k ** 3 if k < .5 else 1 - (-2 * k + 2) ** 3 / 2


def normalise(t, legacy=False):
    """'whip' | {"type": "whip", "beats": .5, "dir": "left", ...} -> dict with type, beats, align, sfx, extras."""
    d = {"type": t} if isinstance(t, str) else dict(t or {"type": "cut"})
    ty = d.get("type", "cut"); ty = ALIASES.get(ty, ty)
    if ty not in TRANSITIONS: raise ValueError(f"unknown transition '{ty}' — {', '.join(TRANSITIONS)}")
    base = TRANSITIONS[ty]
    out = {"type": ty, "beats": float(d.get("beats", base["beats"])), "align": d.get("align", base["align"]),
           "sfx": d.get("sfx", base["sfx"])}
    out.update({k: v for k, v in d.items() if k not in out})
    return out


def window(tr, B):
    d = tr["beats"]
    if tr["align"] == "center": return B - d / 2, B + d / 2
    if tr["align"] == "end": return B - d, B
    return B, B + d


def _pc(pal, rgb01):
    """nearest palette colour (uint8) for an rgb in 0..1."""
    c = pal.colors[((pal.colors - np.asarray(rgb01, np.float32)) ** 2).sum(1).argmin()]
    return (c * 255 + .5).astype(np.uint8)


def _q(pal, x):
    return pal.quantize(np.clip(x / 255.0, 0, 1))


def _bayer(h, w):
    return np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]


def _shift(img, dx, dy, fill):
    h, w = img.shape[:2]; out = np.empty_like(img); out[:] = fill
    dx, dy = int(round(dx)), int(round(dy))
    xs0, xs1 = max(0, -dx), min(w, w - dx); ys0, ys1 = max(0, -dy), min(h, h - dy)
    if xs1 > xs0 and ys1 > ys0: out[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = img[ys0:ys1, xs0:xs1]
    return out


def _warp(img, cx, cy, scale, ang, fill, ocx=None, ocy=None):
    """Nearest-neighbour scale/rotate about (cx,cy) in source, placed at (ocx,ocy) in output."""
    h, w = img.shape[:2]; ocx = cx if ocx is None else ocx; ocy = cy if ocy is None else ocy
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    c, s = math.cos(-ang), math.sin(-ang)
    x = (xx - ocx) / max(scale, 1e-4); y = (yy - ocy) / max(scale, 1e-4)
    sx = c * x - s * y + cx; sy = s * x + c * y + cy
    ix, iy = np.round(sx).astype(int), np.round(sy).astype(int)
    ok = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
    out = np.empty_like(img); out[:] = fill
    out[ok] = img[iy[ok], ix[ok]]
    return out


def _dither_mix(a, b, thr):
    """per-pixel ordered dither between a and b; thr (H×W) in [0,1] = share of b."""
    m = _bayer(*a.shape[:2]) < thr
    out = a.copy(); out[m] = b[m]; return out


def _eye_mask(h, w, r, cx, cy):
    yy, xx = np.mgrid[0:h, 0:w]; x = (xx - cx) / max(r, 1e-3); y = (yy - cy) / max(r * .62, 1e-3)
    return (np.abs(y) <= (1 - np.clip(x * x, 0, 1)) ** 1.0) & (np.abs(x) <= 1)


def apply(tr, a, b, k, pal, ctx):
    """ctx: {"focus_a": (x,y) art px, "focus_b": (x,y), "seed": int, "mask": callable(name)->bool array or None}"""
    ty = tr["type"]; h, w = a.shape[:2]
    bg = (pal.colors[0] * 255 + .5).astype(np.uint8)
    cream = _pc(pal, (.96, .93, .86)).astype(np.float32); hot = _pc(pal, pal.ramp("energy", 1.0)); acc = _pc(pal, pal.ramp("accent", .8))
    k = float(np.clip(k, 0, 1))
    if ty in ("cut", "crash", "match"):
        return b if k >= 0 else a
    if ty == "dissolve":
        yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot((xx - w / 2) / w, (yy - h / 2) / h) / .72
        return _dither_mix(a, b, np.clip(ease(k) * 1.6 - r * .6, 0, 1))
    dir_ = tr.get("dir", "left"); sx, sy = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}[dir_]
    span = w if sx else h
    if ty == "whip":
        e = ease(k); off = e * span * 1.15
        src = a if k < .5 else b; base = -off if k < .5 else span * 1.15 - off
        frames = [_shift(src, sx * (base + j * span * .06), sy * (base + j * span * .06), bg).astype(np.float32) for j in range(-2, 3)]
        sm = sum(frames) / len(frames); blur = math.sin(math.pi * k)
        return _q(pal, src.astype(np.float32) * (1 - blur) + sm * blur * 1.05)
    if ty in ("slide", "push"):
        e = ease(k); out = a.copy() if ty == "slide" else _shift(a, sx * e * span, sy * e * span, bg)
        ox, oy = sx * (e - 1) * span, sy * (e - 1) * span        # new enters from the side opposite to the motion
        nb = _shift(b, ox, oy, bg); m = _shift(np.ones((h, w, 1), np.uint8), ox, oy, 0)[..., 0] > 0
        out[m] = nb[m]; return out
    if ty == "mosaic":
        src = a if k < .5 else b; s = 1 + int(round(14 * (1 - abs(2 * k - 1)) ** 1.5))
        if s <= 1: return src
        hh, ww = (h + s - 1) // s * s, (w + s - 1) // s * s
        pad = np.zeros((hh, ww, 3), np.float32); pad[:h, :w] = src
        blk = pad.reshape(hh // s, s, ww // s, s, 3).mean((1, 3))
        big = np.repeat(np.repeat(blk, s, 0), s, 1)[:h, :w]
        return _q(pal, big)
    if ty == "iris":
        fx, fy = ctx.get("focus_b", (w / 2, h / 2)); r = ease(k) * max(w, h) * 1.25
        m = _eye_mask(h, w, r, fx, fy); m2 = _eye_mask(h, w, r + 2.5, fx, fy)
        out = a.copy(); out[m] = b[m]
        ring = m2 & ~m; out[ring] = hot
        return out
    if ty == "tiles":
        n = int(tr.get("cell", 20)); yy, xx = np.mgrid[0:h, 0:w]
        cxi, cyi = xx // n, yy // n
        delay = (cxi + cyi) / ((w // n) + (h // n) + 1)
        local = np.clip((k * 1.6 - delay * .6) * 2.2 - .2, 0, 1)
        lx = ((xx % n) + .5) / n * 2 - 1; ly = ((yy % n) + .5) / n * 2 - 1
        star = np.minimum(np.maximum(np.abs(lx), np.abs(ly)), (np.abs(lx) + np.abs(ly)) / 1.25)
        m = star < local * 1.25
        edge = (star < local * 1.25 + .14) & ~m & (local > 0) & (local < 1)
        out = a.copy(); out[m] = b[m]; out[edge] = acc
        return out
    if ty == "glitch":
        rng = np.random.default_rng(int(ctx.get("seed", 0)) + int(k * 12))
        amp = math.sin(math.pi * k) * 28; src = (a if k < .5 else b).copy(); oth = b if k < .5 else a
        y = 0
        while y < h:
            bh = int(rng.integers(2, 14)); dx = int(rng.normal(0, amp))
            band = src[y:y + bh] if rng.random() > .25 else oth[y:y + bh]
            src[y:y + bh] = np.roll(band, dx, axis=1); y += bh
        f = src.astype(np.float32); f[..., 0] = np.roll(f[..., 0], int(amp / 6) + 1, 1); f[..., 2] = np.roll(f[..., 2], -int(amp / 6) - 1, 1)
        f[::2] *= 1 - .25 * math.sin(math.pi * k)
        return _q(pal, f)
    if ty == "silhouette":
        mk = ctx.get("mask")
        m = mk(tr.get("shape", "circle"), tr.get("size", .62)) if mk else _eye_mask(h, w, w * .35, w / 2, h / 2)
        glow = np.zeros_like(a); glow[:] = _pc(pal, pal.ramp("energy", .9))
        if k < .5:
            kk = ease(k * 2); fill = _dither_mix(a, glow, np.full((h, w), kk))
            out = a.copy(); out[m] = fill[m]; return out
        kk = ease((k - .5) * 2)
        outside = _dither_mix(a, b, np.full((h, w), min(1, kk * 1.6)))
        inside = _dither_mix(glow, b, np.full((h, w), max(0, kk * 1.6 - .6)))
        out = outside.copy(); out[m] = inside[m]; return out
    if ty == "flash":
        # peak capped (default .88): the drop still whites out, but no frame is a flat featureless cream card
        src = (a if k < .5 else b).astype(np.float32); f = (1 - abs(2 * k - 1)) * float(tr.get("peak", .88))
        return _q(pal, src * (1 - f) + cream * f)
    if ty == "spin":
        if tr.get("over"):          # old frame spins away ON TOP of the new one (no black gap); new brightens in from a dither
            e = ease(k); old = _warp(a, w / 2, h / 2, max(.02, 1 - e), e * math.pi * .9, bg)
            hole = np.all(old == bg, axis=2) & ~np.all(_warp(np.ones_like(a), w / 2, h / 2, max(.02, 1 - e), e * math.pi * .9, 0) == 1, axis=2)
            under = _dither_mix(np.broadcast_to(bg, a.shape).copy(), b, np.full((h, w), .35 + .65 * e, np.float32))
            out = old.copy(); out[hole] = under[hole]
            return out if k < 1 else b
        if k < .5: e = ease(k * 2); return _warp(a, w / 2, h / 2, 1 - .95 * e, e * math.pi * .75, bg)
        e = ease((k - .5) * 2); return _warp(b, w / 2, h / 2, .05 + .95 * e, -(1 - e) * math.pi * .75, bg)
    if ty == "split":
        div = h // 2; line = hot
        if k < .2: top = div + int((1 - ease(k / .2)) * (h - div))       # new half slides up from below
        elif k < .7: top = div                                           # hold: old (top) vs new (bottom)
        else: top = int(div * (1 - ease((k - .7) / .3)))                 # new takes over
        out = np.empty_like(a)
        if top > 0: out[:top] = a[(h - top) // 2:(h - top) // 2 + top]   # centre crops keep both subjects in view
        if top < h: out[top:] = b[top // 2:top // 2 + (h - top)]
        if 0 < top < h: out[max(0, top - 1):top + 1] = line
        return out
    if ty == "portal":
        # the outgoing scene's dive is a live camera move (render.Film.camera), the incoming scene brings its own
        # camera move: no bitmap scaling here, so pixels stay square/1:1 and no black frame shows around a shrunk copy
        e = k * k
        old, new = a, b
        r = e * math.hypot(w, h) * .75
        yy, xx = np.mgrid[0:h, 0:w]; d = np.hypot(xx - w / 2, yy - h / 2)
        out = old.copy(); m = d < r; out[m] = new[m]
        ring = (d >= r) & (d < r + 2) & (r > 1); out[ring] = hot
        return out
    if ty == "crt":
        src = a if k < .5 else b; p = (k * 2) if k < .5 else (2 - k * 2)    # 0 = full picture, 1 = off
        out = np.empty_like(a); out[:] = bg
        fl = float(tr.get("floor", 0))     # >0: a dimmed after-image stays behind the collapse (no near-black frames)
        if fl > 0: out[:] = _q(pal, src.astype(np.float32) * fl * (1 - .4 * p))
        if p < .7:
            sy_ = max(1e-3, 1 - p / .7); hh = max(1, int(h * sy_))
            rows = (np.arange(hh) / sy_ + (h - hh / sy_) / 2).astype(int).clip(0, h - 1)
            y0 = (h - hh) // 2
            f = src[rows].astype(np.float32) * (1 + 1.2 * p)
            out[y0:y0 + hh] = _q(pal, f)
        else:
            q = (p - .7) / .3; ww = max(1, int(w * (1 - q))); x0 = (w - ww) // 2
            out[h // 2 - 1:h // 2 + 1, x0:x0 + ww] = cream.astype(np.uint8)
        return out
    raise ValueError(ty)
