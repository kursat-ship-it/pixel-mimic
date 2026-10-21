"""Masks for silhouettes / objects: built-in shapes, a glyph from the pixel font, or a user PNG (alpha or luminance)."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_PATHS = ["/usr/share/fonts/truetype/sand-box/google/Press Start 2P/PressStart2P-Regular.ttf",
              os.path.join(os.path.dirname(__file__), "assets", "PressStart2P-Regular.ttf")]


def font_path():
    for p in FONT_PATHS:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("Press Start 2P not found; put PressStart2P-Regular.ttf in bitloop/assets/")


def _poly(d, pts, S):
    d.polygon([(S / 2 + x * S / 2, S / 2 + y * S / 2) for x, y in pts], fill=255)


def builtin(name, S=256):
    im = Image.new("L", (S, S), 0); d = ImageDraw.Draw(im)
    if name == "circle":
        d.ellipse([S * .08, S * .08, S * .92, S * .92], fill=255)
    elif name == "heart":
        pts = [(16 * math.sin(t) ** 3 / 17, -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 17)
               for t in np.linspace(0, 2 * math.pi, 120)]
        _poly(d, pts, S)
    elif name == "drop":
        pts = [((math.sin(t) * (1 - math.cos(t)) * .5) * 1.1, -math.cos(t) * .9) for t in np.linspace(0, 2 * math.pi, 120)]
        _poly(d, pts, S)
    elif name == "star":
        pts = [((.9 if i % 2 == 0 else .38) * math.sin(i * math.pi / 5), -(.9 if i % 2 == 0 else .38) * math.cos(i * math.pi / 5)) for i in range(10)]
        _poly(d, pts, S)
    elif name == "bolt":
        _poly(d, [(.15, -.95), (-.45, .1), (-.05, .1), (-.2, .95), (.5, -.15), (.08, -.15), (.3, -.95)], S)
    elif name == "hexagon":
        _poly(d, [(.9 * math.cos(a), .9 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 7)[:-1]], S)
    elif name == "cloud":
        for cx, cy, r in [(-.45, .15, .35), (0, -.1, .45), (.45, .15, .35), (0, .25, .35)]:
            d.ellipse([S / 2 + (cx - r) * S / 2, S / 2 + (cy - r) * S / 2, S / 2 + (cx + r) * S / 2, S / 2 + (cy + r) * S / 2], fill=255)
    elif name == "square":
        d.rectangle([S * .12, S * .12, S * .88, S * .88], fill=255)
    else:
        raise ValueError(f"unknown shape '{name}' (circle heart drop star bolt hexagon cloud square, glyph:X, or a .png path)")
    return np.asarray(im) > 127


def glyph(ch, S=256):
    """A character of the built-in pixel font as a mask (e.g. 'glyph:Ş', 'glyph:?', 'glyph:7')."""
    from .pixfont import GLYPHS, norm
    from .captions import upper
    g = GLYPHS.get(norm(upper(ch))[:1] or "?", GLYPHS["?"])
    g = g[:, :] if g[:2].any() or g[9].any() else g[2:9]
    k = int(S * .8 / max(g.shape)); big = np.kron(g, np.ones((k, k), bool))
    out = np.zeros((S, S), bool); y, x = (S - big.shape[0]) // 2, (S - big.shape[1]) // 2
    out[y:y + big.shape[0], x:x + big.shape[1]] = big
    return out


def from_png(path, S=256):
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im)[..., 3]
    if a.min() == 255:  # no alpha → use luminance (bright = inside)
        a = np.asarray(im.convert("L"))
    im = Image.fromarray(a); im.thumbnail((S, S))
    pad = Image.new("L", (S, S), 0); pad.paste(im, ((S - im.width) // 2, (S - im.height) // 2))
    return np.asarray(pad) > 127


def load_mask(spec, base_dir="."):
    if spec.startswith("glyph:"):
        return glyph(spec[6:])
    if spec.lower().endswith(".png") or spec.lower().endswith(".jpg"):
        p = spec if os.path.isabs(spec) else os.path.join(base_dir, spec)
        return from_png(p)
    return builtin(spec)


class Mask:
    """Binary mask placed in world space: centre (x,y), size (world units across)."""
    def __init__(self, arr, x=0, y=0, size=100):
        self.a, self.x, self.y, self.size = arr, x, y, size
        self.S = arr.shape[0]

    def test(self, wx, wy):
        u = ((wx - self.x) / self.size + .5) * self.S; v = ((wy - self.y) / self.size + .5) * self.S
        ok = (u >= 0) & (u < self.S) & (v >= 0) & (v < self.S)
        return ok & self.a[np.clip(v.astype(int), 0, self.S - 1), np.clip(u.astype(int), 0, self.S - 1)]

    def sample(self, n, rng):
        ys, xs = np.nonzero(self.a)
        i = rng.integers(0, len(xs), n)
        jx, jy = rng.random(n), rng.random(n)
        return (self.x + ((xs[i] + jx) / self.S - .5) * self.size, self.y + ((ys[i] + jy) / self.S - .5) * self.size)
