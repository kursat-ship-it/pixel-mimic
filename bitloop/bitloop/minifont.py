"""3×5 micro pixel font for in-world labels that must stay tiny (scope labels, tree values, record labels, chalk
handles). Upper-case + digits + basic math punctuation; lower-case input is upper-cased (Turkish-aware for i/ı).
Turkish capitals İ Ş Ğ Ü Ö Ç get their mark in an extra row above/below (cell = 3×7 incl. accent rows)."""
import numpy as np

_M = {
 "A": "###|#.#|###|#.#|#.#", "B": "##.|#.#|##.|#.#|##.", "C": "###|#..|#..|#..|###", "D": "##.|#.#|#.#|#.#|##.",
 "E": "###|#..|##.|#..|###", "F": "###|#..|##.|#..|#..", "G": "###|#..|#.#|#.#|###", "H": "#.#|#.#|###|#.#|#.#",
 "I": "###|.#.|.#.|.#.|###", "J": "..#|..#|..#|#.#|###", "K": "#.#|#.#|##.|#.#|#.#", "L": "#..|#..|#..|#..|###",
 "M": "#.#|###|###|#.#|#.#", "N": "##.|#.#|#.#|#.#|#.#", "O": "###|#.#|#.#|#.#|###", "P": "##.|#.#|##.|#..|#..",
 "Q": "###|#.#|#.#|###|..#", "R": "##.|#.#|##.|#.#|#.#", "S": "###|#..|###|..#|###", "T": "###|.#.|.#.|.#.|.#.",
 "U": "#.#|#.#|#.#|#.#|###", "V": "#.#|#.#|#.#|#.#|.#.", "W": "#.#|#.#|###|###|#.#", "X": "#.#|#.#|.#.|#.#|#.#",
 "Y": "#.#|#.#|.#.|.#.|.#.", "Z": "###|..#|.#.|#..|###",
 "0": "###|#.#|#.#|#.#|###", "1": ".#.|##.|.#.|.#.|###", "2": "###|..#|###|#..|###", "3": "###|..#|.##|..#|###",
 "4": "#.#|#.#|###|..#|..#", "5": "###|#..|###|..#|###", "6": "###|#..|###|#.#|###", "7": "###|..#|.#.|.#.|.#.",
 "8": "###|#.#|###|#.#|###", "9": "###|#.#|###|..#|###",
 "-": "...|...|###|...|...", "+": "...|.#.|###|.#.|...", "=": "...|###|...|###|...", ".": "...|...|...|...|.#.",
 ":": "...|.#.|...|.#.|...", "/": "..#|..#|.#.|#..|#..", "(": ".#.|#..|#..|#..|.#.", ")": ".#.|..#|..#|..#|.#.",
 ">": "#..|.#.|..#|.#.|#..", "<": "..#|.#.|#..|.#.|..#", "!": ".#.|.#.|.#.|...|.#.", "?": "###|..#|.##|...|.#.",
 "@": "###|#.#|#.#|#..|###", "%": "#.#|..#|.#.|#..|#.#", "'": ".#.|.#.|...|...|...", "_": "...|...|...|...|###",
 "∞": "...|...|#.#|.#.|#.#", "·": "...|...|.#.|...|...",
}
_ACC = {"İ": ("I", ".#.", None), "Ö": ("O", "#.#", None), "Ü": ("U", "#.#", None), "Ğ": ("G", "###", None),
        "Ç": ("C", None, ".#."), "Ş": ("S", None, ".#.")}
GLYPHS = {}
for ch, s in _M.items():
    a = np.zeros((7, 3), bool)
    for r, line in enumerate(s.split("|")): a[1 + r] = [c == "#" for c in line]
    GLYPHS[ch] = a
for ch, (base, top, bot) in _ACC.items():
    a = GLYPHS[base].copy()
    if top: a[0] = [c == "#" for c in top]
    if bot: a[6] = [c == "#" for c in bot]
    GLYPHS[ch] = a
GLYPHS[" "] = np.zeros((7, 2), bool)
GLYPHS[","] = GLYPHS["."].copy(); GLYPHS[","][6] = [True, False, False]         # decimal comma (Turkish numbers)
for _k, _rows in (("μ", "#.#|#.#|#.#|##.|#.."), ("ν", "#.#|#.#|#.#|#.#|.#."), ("π", "###|#.#|#.#|#.#|#.#")):   # math subscripts
    _a = np.zeros((7, 3), bool)
    for _r, _line in enumerate(_rows.split("|")): _a[1 + _r] = [c == "#" for c in _line]
    GLYPHS[_k] = _a; GLYPHS[_k.upper()] = _a


def _up(text):
    return text.replace("i", "İ").replace("ı", "I").upper()


def mini_bitmap(text, upper=True):
    """→ bool array (7·lines − 2 rows trimmed to ink, W cols) for multi-line text, lines centred, 1-col tracking."""
    lines = (_up(text) if upper else text).split("\n")
    rows = []
    for l in lines:
        cols = []
        for ch in l:
            cols += [GLYPHS.get(ch, GLYPHS["?"]), np.zeros((7, 1), bool)]
        rows.append(np.concatenate(cols[:-1], 1) if cols else np.zeros((7, 1), bool))
    w = max(r.shape[1] for r in rows); out = np.zeros((7 * len(rows), w), bool)
    for i, r in enumerate(rows):
        x = (w - r.shape[1]) // 2; out[i * 7:i * 7 + 7, x:x + r.shape[1]] = r
    ink = np.nonzero(out.any(1))[0]
    return out[ink.min():ink.max() + 1] if len(ink) else out


def draw_mini(cv, text, x, y, dot, color, alpha=1.0, rot=0.0, upper=True, snap=False):
    """Micro text centred at world (x, y); dot = world units per font dot. Crisp at any camera zoom."""
    from .bitmap import Bitmap, draw_bitmap
    bm = Bitmap(mini_bitmap(text, upper), x, y, dot, rot)
    draw_bitmap(cv, bm, color, alpha, snap=snap)
    return bm
