"""Vision modes: how a creature's eye turns the scene G-buffer into display colour.

A vision segment renders the world ONCE into a G-buffer (Canvas.rgb albedo + aux planes uv / temp / depth / oid) and
then maps it through the segment's mode, quantised to the mode's own locked palette:

    spec.visions = {mode: {"map": <MAPS key>, "palette": name|dict, "pixel": 1|2, "blur": σ, "label": ..., ...}}
    segment.vision = mode   (a name that is only a PALETTES entry, e.g. "hayret", = map "rgb" in that palette)

Maps (formulas from projects/canli-gozu/vision_mock.py, the reference):
  rgb               plain albedo (trichromat baseline)
  bee_false_colour  R ← .82G + .18R (bee 'green'), G ← .95B (bee 'blue'), B ← uv (bee UV) — UV-photo convention
  dichromat         Machado 2009 deuteranopia matrix in ~linear light (γ 2.2); use with pixel 2 (acuity)
  thermal           gaussian(temp, blur) → ramp 'body' ^.9, ×.82 + .18·lum·pale[.3] (pit-organ heat + eye edges)
  sonar             echo map: Sobel(depth) > .08 ∪ oid edges + .55 iso-depth contours, lit by expanding rings
                    (ctx["rings"] = [(radius_px, weight)], ctx["origin"] = screen px, ctx["base"] = steady edge level); sky ×.15; faint wavefront in air
  bands12           12 saturated hue bands (+ strong UV = its own violet band), V in 3 steps
  coarse_classes    5 flat broad colour classes; low saturation → dark violet grey
  tint              lum-tinted night (brand night look)
"""
import numpy as np
from .palette import Palette, PALETTES, BAYER4

MAPS = ("rgb", "bee_false_colour", "dichromat", "thermal", "sonar", "bands12", "coarse_classes", "tint")
MACHADO_DEUTAN = np.array([[.367322, .860646, -.227968], [.280085, .672501, .047413], [-.011820, .042940, .968881]], np.float32)
COARSE = ["#E0503A", "#E8C838", "#4FCB6A", "#3F6FD8", "#B048D8"]
COARSE_GREY = "#2E2456"
LUM = np.array([.3, .59, .11], np.float32)


def _hx(h):
    h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


class Vision:
    """A resolved vision mode: map + Palette + options."""
    def __init__(self, name, d):
        self.name = name; self.d = dict(d)
        self.map = d.get("map", "rgb")
        if self.map not in MAPS: raise ValueError(f"vision '{name}': unknown map '{self.map}' ({', '.join(MAPS)})")
        self.pal = Palette(d.get("palette", "hayret"))
        self.pixel = int(d.get("pixel", 1)); self.blur = float(d.get("blur", 2.0))
        self.spread = float(d.get("spread", .11))


def resolve(spec, name):
    """mode name -> Vision (None for None). Unknown names that are palettes = plain rgb in that palette."""
    if name is None: return None
    vs = spec.get("visions") or {}
    if name in vs: return Vision(name, vs[name])
    if name in PALETTES: return Vision(name, {"map": "rgb", "palette": name})
    raise ValueError(f"unknown vision '{name}' (spec.visions: {', '.join(vs) or '—'}; or a palette name)")


# ------------------------------------------------------------------ helpers
def rgb2hsv(c):
    mx = c.max(-1); mn = c.min(-1); d = mx - mn + 1e-6
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
    return h, np.where(mx > 0, d / (mx + 1e-6), 0), mx


def hsv2rgb(h, s, v):
    i = np.floor(h * 6).astype(int) % 6; f = h * 6 - np.floor(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    sel = [np.stack(x, -1) for x in [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]]
    out = np.zeros(h.shape + (3,), np.float32)
    for k in range(6): out[i == k] = sel[k][i == k]
    return out


def edges(depth, oid):
    from scipy.ndimage import sobel
    e = (np.abs(sobel(depth, 0)) + np.abs(sobel(depth, 1))) > .08
    o = oid.astype(np.float32)
    e |= (np.abs(sobel(o, 0)) + np.abs(sobel(o, 1))) > 0
    return e


def apply(v, G, ctx=None):
    """G = {"rgb" (H,W,3 albedo 0..1), "uv", "temp", "depth", "oid"} -> display rgb (H,W,3) float for Vision v."""
    ctx = ctx or {}
    alb = np.clip(G["rgb"], 0, 1); uv, temp, depth, oid = G["uv"], G["temp"], G["depth"], G["oid"]
    H, W = depth.shape; sky = oid == 0; pal = v.pal; m = v.map
    if m == "rgb": return alb.copy()
    if m == "bee_false_colour":
        return np.stack([.82 * alb[..., 1] + .18 * alb[..., 0], alb[..., 2] * .95, uv], -1)
    if m == "dichromat":
        return np.clip((alb ** 2.2) @ MACHADO_DEUTAN.T, 0, 1) ** (1 / 2.2)
    if m == "thermal":
        from scipy.ndimage import gaussian_filter
        th = gaussian_filter(temp, v.blur) if v.blur > 0 else temp
        lum = alb @ LUM
        d = pal.ramp("body", np.clip((th - .05) / .95, 0, 1) ** .9)
        return d * .82 + .18 * lum[..., None] * pal.ramp("pale", .3)
    if m == "sonar":
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32) + .5
        ox, oy = ctx.get("origin", (W * .25, H * .33)); dist = np.hypot(xx - ox, yy - oy)
        lv = np.floor(depth * 10)
        e = edges(depth, oid).astype(np.float32) + .55 * ((lv != np.roll(lv, 1, 0)) & (depth < .9))
        ring = np.zeros_like(dist); trail = np.zeros_like(dist); front = np.zeros_like(dist)
        for R, w in ctx.get("rings", []):
            ring = np.maximum(ring, np.exp(-((dist - R) / 7) ** 2) * w)
            trail = np.maximum(trail, np.where(dist < R, np.exp(-(R - dist) / 70), 0) * w)
            front = np.maximum(front, np.exp(-((dist - R) / 2.0) ** 2) * w)
        solid = (depth < .9).astype(np.float32)
        base = float(ctx.get("base", 0.0))         # steady faint echo map (e.g. a mosaic tile between clicks)
        echo = np.clip(e * (ring + trail * .75 + base) + .10 * solid * trail + .05 * solid, 0, 1)
        echo[sky] *= .15
        d = np.where(echo[..., None] > .02, pal.ramp("body", echo), pal.ramp("bg", np.zeros_like(echo)))
        return d + front[..., None] * .25 * (depth[..., None] > .95)
    if m in ("bands12", "coarse_classes"):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        h, s, val = rgb2hsv(alb)
        hu = np.where((uv > .85) & ~sky, .80 + .12 * uv, h)
        if m == "bands12":
            hu = (hu + .035 * np.sin(xx / 7 + yy / 11)) % 1
            hb = np.floor(hu * 12) / 12 + 1 / 24; vb = np.clip(np.ceil(val * 3) / 3, .34, 1)
            return hsv2rgb(hb % 1, np.ones_like(h), vb)
        cls = np.array([_hx(c) for c in COARSE])
        k = np.digitize(hu % 1, [.06, .2, .45, .7, .9]) % 5
        d = cls[k] * np.where(val < .25, .35, 1)[..., None]
        lo = s < .18
        d[lo] = _hx(COARSE_GREY) * .6 + .4 * (val[lo][..., None] > .7)
        return d
    if m == "tint":
        lum = alb @ LUM; return lum[..., None] * np.array([.55, .7, 1.0], np.float32) * .75
    raise ValueError(m)


def quantize(rgb, pal, pixel=1, spread=.11):
    """Screen-anchored Bayer quantise to pal; pixel 2 = 2×2 block average + coarse Bayer (lower acuity)."""
    if pixel <= 1: return pal.quantize(np.clip(rgb, 0, 1), spread)
    H, W, _ = rgb.shape; hh, ww = H // pixel, W // pixel
    d = np.clip(rgb[:hh * pixel, :ww * pixel], 0, 1).reshape(hh, pixel, ww, pixel, 3).mean((1, 3))
    by = np.tile(BAYER4, (hh // 4 + 1, ww // 4 + 1))[:hh, :ww]
    x = d + (by[..., None] - .5) * spread
    idx = ((x[:, :, None, :] - pal.colors[None, None]) ** 2).sum(-1).argmin(-1)
    small = (pal.colors[idx] * 255 + .5).astype(np.uint8)
    out = np.repeat(np.repeat(small, pixel, 0), pixel, 1)
    if out.shape[:2] != (H, W):
        full = pal.quantize(np.clip(rgb, 0, 1), spread); full[:out.shape[0], :out.shape[1]] = out; out = full
    return out


def dither_mix(a, b, share):
    """Ordered (Bayer 4×4, screen-anchored) dither: share of pixels taken from b; share scalar or (H,W)."""
    H, W = a.shape[:2]
    by = np.tile(BAYER4, (H // 4 + 1, W // 4 + 1))[:H, :W]
    m = by < share
    out = a.copy(); out[m] = b[m]; return out


def union_palette(pals, ramps_from):
    """Palette holding every colour of pals (transitions between two modes stay palette-safe for both)."""
    cols = []
    for p in pals:
        for c in p.colors:
            if not any(np.allclose(c, q) for q in cols): cols.append(c)
    u = Palette.__new__(Palette)
    u.__dict__.update(ramps_from.__dict__); u.colors = np.array(cols, np.float32); u.name = "union"
    return u
