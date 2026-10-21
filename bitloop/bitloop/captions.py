"""Top-centred black-box captions in a pixel font, rendered at full resolution (crisp on phones).
Locked from the reference: ALL CAPS, 1–3 lines, box top at ~9.7 % of the height, key-number line in amber,
~0.1 s dithered fade in/out (text ghosts in first, then the box)."""
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .shapes import font_path
from .palette import BAYER4


def upper(text, lang="tr"):
    if lang == "tr":
        text = text.replace("i", "İ").replace("ı", "I")
    return text.upper()


class CaptionStyle:
    def __init__(self, W, H, pal, size=None, top=None, pad=(24, 18), line_gap=1.45, max_w=None, lang="tr", grid=6):
        self.W, self.H, self.lang, self.grid = W, H, lang, grid
        self.dot = size or max(4, round(W * 12 / 1080))                 # 12 px per font dot at 1080 wide (reference)
        self.top = top if top is not None else int(H * 186 / 1920)
        self.pad, self.line_gap = pad, line_gap
        self.max_w = max_w or int(W * 0.93)
        self.box, self.fg, self.hi = pal.caption["box"], pal.caption["text"], pal.caption["hi"]


def parse(text, hi_lines=()):
    """Lines split on '\\n' or '/'. Highlight: whole lines via hi_lines (1-based) or inline *spans*."""
    lines = [l.strip() for l in re.split(r"\n|\s/\s", text) if l.strip()]
    out = []
    for i, l in enumerate(lines, 1):
        parts = re.split(r"(\*[^*]+\*)", l)
        segs = [(p[1:-1], True) if p.startswith("*") else (p, i in hi_lines) for p in parts if p]
        out.append(segs)
    return out


def render(text, st, hi_lines=()):
    """→ (RGBA uint8 array, x, y, dot) for the caption block, drawn with the 5×7 bitmap font."""
    from .pixfont import line_bitmap
    lines = parse(upper(text, st.lang), hi_lines)
    bms = [line_bitmap(segs) for segs in lines]
    dot = st.dot
    wmax = max(b[0].shape[1] for b in bms)
    while wmax * dot + 2 * st.pad[0] > st.max_w and dot > 5:      # 5 = narration.MIN_DOT (legible floor)
        dot -= 1
    top_acc = bms[0][0][:2].any(); bot_acc = bms[-1][0][9].any()
    rows = 10 * len(bms)
    r0 = 0 if top_acc else 2; r1 = rows if bot_acc else rows - 1
    bw = wmax * dot + 2 * st.pad[0]; bh = (r1 - r0) * dot + 2 * st.pad[1]
    g = st.grid; bw += (-bw) % g; bh += (-bh) % g
    off = r0 * dot                                   # draw on a canvas that also holds the unused accent rows
    arr = np.empty((bh + off, bw, 4), np.uint8); arr[:] = st.box + (255,)
    for i, (m, h) in enumerate(bms):
        x0 = (bw - m.shape[1] * dot) // 2; y0 = st.pad[1] + i * 10 * dot
        big = np.kron(m, np.ones((dot, dot), bool)); bigh = np.kron(h, np.ones((dot, dot), bool))
        reg = arr[y0:y0 + big.shape[0], x0:x0 + big.shape[1]]
        big, bigh = big[:reg.shape[0], :reg.shape[1]], bigh[:reg.shape[0], :reg.shape[1]]
        reg[big & ~bigh] = st.fg + (255,); reg[big & bigh] = st.hi + (255,)
    arr = np.ascontiguousarray(arr[off:off + bh])
    x0 = (st.W - bw) // 2; x0 -= x0 % g
    return arr, x0, st.top, dot


def coverage(text, lang="tr"):
    """Characters the caption font cannot draw (for validation)."""
    from .pixfont import missing
    return missing(upper(text, lang).replace("*", ""))


class CaptionTrack:
    """All captions of the film; composite(frame, t) draws the visible ones with dithered fades."""
    def __init__(self, items, st, fade=0.1):
        self.st, self.fade = st, fade
        self.items = []
        for it in items:
            arr, x, y, size = render(it["text"], st, it.get("hi", ()))
            self.items.append(dict(it, arr=arr, x=x, y=y, dot=size))
        g = st.grid
        self._bay = {}

    def _bayer(self, h, w):
        key = (h, w)
        if key not in self._bay:
            g = self.st.grid
            b = np.kron(np.tile(BAYER4, (h // (4 * g) + 2, w // (4 * g) + 2)), np.ones((g, g), np.float32))
            self._bay[key] = b[:h, :w]
        return self._bay[key]

    def alpha(self, it, t):
        a0, a1 = it["t0"], it["t1"]
        if t < a0 or t > a1: return 0.0
        fi = 1.0 if it.get("no_fade_in") else min(1.0, (t - a0) / self.fade)
        fo = 1.0 if it.get("no_fade_out") else min(1.0, (a1 - t) / self.fade)
        return max(0.0, min(fi, fo))

    def composite(self, frame, t):
        for it in self.items:
            k = self.alpha(it, t)
            if k <= 0: continue
            arr, x, y = it["arr"], it["x"], it["y"]
            h, w = arr.shape[:2]
            reg = frame[y:y + h, x:x + w]
            h, w = reg.shape[:2]
            a = arr[:h, :w]
            if k >= 1:
                reg[:] = a[..., :3]; continue
            bay = self._bayer(h, w)
            text = (a[..., :3].astype(int).sum(-1) > sum(self.st.box) + 60)
            show_text = text & (bay < min(1, k * 1.6))       # text ghosts in first
            show_box = (~text) & (bay < k ** 1.5 * .95)        # then the box fills
            m = show_text | show_box
            reg[m] = a[..., :3][m]
        return frame
