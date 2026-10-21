"""World-space bitmaps (text / logo mark) sampled per art pixel, with optional rotation — used by brand props."""
import math
import numpy as np
from .pixfont import line_bitmap, mark_layers, MARK_ROLES


def text_bitmap(text, upper=False):
    from .captions import upper as up
    lines = text.split("\n")
    bms = [line_bitmap([(up(l) if upper else l, False)])[0] for l in lines]
    w = max(b.shape[1] for b in bms); out = np.zeros((10 * len(bms), w), bool)
    for i, b in enumerate(bms):
        x = (w - b.shape[1]) // 2; out[i * 10:i * 10 + 10, x:x + b.shape[1]] = b
    rows = np.nonzero(out.any(1))[0]
    return out[rows.min():rows.max() + 1] if len(rows) else out


class Bitmap:
    """bool array placed in world space: centre (x,y), `dot` world units per dot, rotation in degrees."""
    def __init__(self, arr, x=0.0, y=0.0, dot=1.0, rot=0.0):
        self.a, self.x, self.y, self.dot = arr, x, y, dot
        self.h, self.w = arr.shape; self.c, self.s = math.cos(math.radians(-rot)), math.sin(math.radians(-rot))

    @property
    def size(self): return self.w * self.dot, self.h * self.dot

    def test(self, wx, wy):
        dx, dy = wx - self.x, wy - self.y
        rx, ry = self.c * dx - self.s * dy, self.s * dx + self.c * dy
        u = rx / self.dot + self.w / 2; v = ry / self.dot + self.h / 2
        ok = (u >= 0) & (u < self.w) & (v >= 0) & (v < self.h)
        return ok & self.a[np.clip(v.astype(int), 0, self.h - 1), np.clip(u.astype(int), 0, self.w - 1)]


def _draw_snapped(cv, bm, color, alpha):
    """Pixel-exact stamp: every font dot = exactly k×k art pixels (k = round(dot·zoom) ≥ 1), top-left on the art
    grid. Used for small in-world text that must stay legible while the camera zooms (no dropped/doubled columns)."""
    k = max(1, int(round(bm.dot * cv.cam.zoom)))
    X, Y = cv.to_screen(bm.x, bm.y)
    x0, y0 = int(round(float(X) - bm.w * k / 2)), int(round(float(Y) - bm.h * k / 2))
    big = np.repeat(np.repeat(bm.a, k, 0), k, 1).astype(np.float32) * alpha
    H, W = cv.rgb.shape[:2]
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + big.shape[1]), min(H, y0 + big.shape[0])
    if xa >= xb or ya >= yb: return
    cv._blend((slice(ya, yb), slice(xa, xb)), big[ya - y0:yb - y0, xa - x0:xb - x0], cv._col(color))


def draw_bitmap(cv, bm, color, alpha=1.0, bbox_pad=2, snap=False):
    """Fill only inside the bitmap's screen bbox (fast). snap=True: pixel-exact integer-scale stamp (upright only)."""
    # snap only where sampling hurts most (≈1 art px per dot); at ≥1.75 px/dot (e.g. a fast camera dive) normal
    # sampling keeps the text's size continuous with the object it is printed on
    if snap and bm.dot * cv.cam.zoom < 1.75 and abs(bm.s) < 1e-6 and abs(getattr(cv, "_s", 0.0)) < 1e-3:
        return _draw_snapped(cv, bm, color, alpha)
    X, Y = cv.to_screen(bm.x, bm.y); R = cv.sl(max(bm.size)) * .75 + bbox_pad
    b = cv._box(X, Y, R)
    if b is None: return
    wx, wy = cv.world_grid()
    m = bm.test(wx[b], wy[b]).astype(np.float32) * alpha
    cv._blend(b, m, cv._col(color))


def draw_text(cv, text, x, y, dot, color, alpha=1.0, rot=0.0, glow=0.0, upper=False, snap=False):
    bm = Bitmap(text_bitmap(text, upper), x, y, dot, rot)
    if glow > 0:
        w, h = bm.size; cv.glow(x, y, max(w, h) * .45, color, glow * .5)
    draw_bitmap(cv, bm, color, alpha, snap=snap)
    return bm


def draw_mark(cv, pal, x, y, dot, alpha=1.0, rot=0.0, glow=0.35, mono=None, outline=None, snap=False):
    """The hayret.piksel 'wonder eye' mark. mono=colour draws it single-colour (stamps, etchings)."""
    L = mark_layers()
    if glow > 0: cv.glow(x, y, 7 * dot, pal.ramp("energy", .7), glow)
    for ch, (ramp, t) in MARK_ROLES.items():
        if mono is not None and ch == "k": continue
        col = mono if mono is not None else (outline if (outline is not None and ch == "o") else pal.ramp(ramp, t))
        draw_bitmap(cv, Bitmap(L[ch], x, y, dot, rot), col, alpha, snap=snap)


def formula_bitmap(text, scale=2):
    """Math notation with real sub/superscripts: "G_{μν} = 8πG T_{μν}", "E = mc^{2}".
    scale=2: normal runs are the pixfont at 2× (2 dots per font dot), `_{..}` / `^{..}` runs the pixfont at 1×
    lowered/raised; draw with dot = ½ of the normal text dot (needs ≥ 2 art px per normal font dot).
    scale=1: normal runs at 1×, scripts in the 3×5 minifont (Greek μ ν π included); draw at the normal dot, so it
    works at 1 art px per dot (chalkboards, signs). → bool array (rows trimmed)."""
    import re
    from .minifont import mini_bitmap
    parts = re.split(r"([_^])\{([^}]*)\}", text)
    runs = []; i = 0
    while i < len(parts):
        if parts[i]: runs.append(("n", parts[i]))
        if i + 2 < len(parts): runs.append(("sub" if parts[i + 1] == "_" else "sup", parts[i + 2]))
        i += 3
    H = 26 if scale == 2 else 14; cols = []
    for kind, s_ in runs:
        if kind == "n":
            b = line_bitmap([(s_, False)])[0]
            if scale == 2: b = np.kron(b, np.ones((2, 2), bool))
            top = 3 if scale == 2 else 1
        elif scale == 2:
            b = line_bitmap([(s_, False)])[0]; top = 13 if kind == "sub" else 0
        else:
            b = mini_bitmap(s_); top = 8 if kind == "sub" else 0
        c = np.zeros((H, b.shape[1] + (1 if kind != "n" else 0)), bool)
        c[top:top + b.shape[0], :b.shape[1]] = b[:H - top]
        cols.append(c)
    out = np.concatenate(cols, 1) if cols else np.zeros((H, 1), bool)
    rows = np.nonzero(out.any(1))[0]
    return out[rows.min():rows.max() + 1] if len(rows) else out
