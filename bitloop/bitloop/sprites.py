"""Multi-colour pixel sprites (hand-drawn char maps) and the recurring mascot: the hooded hero ("Kâşif").
A sprite is a list of equal-length strings; each char is a colour role ('.' = transparent). Roles map to exact
palette colours (no dithering on the character), so he stays crisp and readable at phone size.
Frames are designed on a 16×22 grid; feet are on the bottom row, the sprite anchor is bottom-centre."""
import numpy as np
from .bitmap import Bitmap, draw_bitmap

# role → Çini Gecesi colour
ROLES = {
    "o": "#060814",   # ink outline (Gece)
    "c": "#2C47A6",   # cloak (Kobalt)
    "d": "#1E2E73",   # cloak shadow (Kobalt Koyu)
    "r": "#77A2EE",   # rim light (Gök)
    "f": "#F4ECDC",   # face / hands (Krem)
    "g": "#B8CDF2",   # face shade (Sis)
    "e": "#060814",   # eyes
    "w": "#D2FFF5",   # eye sparkle (Parıltı)
    "p": "#FF9A86",   # blush (Mercan Işık)
    "s": "#EC4A57",   # scarf / tassel (Çini Mercanı)
    "k": "#7E1F35",   # scarf shade (Kiremit)
    "b": "#141E4A",   # boots (Mürekkep)
    "t": "#41E8D2",   # türkuaz (lantern / book light)
}

HERO = {
 # facing camera, eyes open
 "front": [
  "......oooo......",
  ".....occcco.....",
  "....occccrco....",
  "...occcccrcco...",
  "..occcoooocrco..",
  "..occoffffforo..",
  ".occofffffffoco.",
  ".occofefffefoco.",
  ".occofefffefoco.",
  ".occopfffffpoco.",
  "..occogffffgoco.",
  "..oocccoooocco..",
  ".occcssssssscco.",
  ".occckksssskcco.",
  "occcdccsscccrcco",
  "occcdcccccccrcco",
  "occcdcccccccrcco",
  "occcdccccccrccco",
  ".occdcccccccrco.",
  ".oodddddddddroo.",
  "..obbo....obbo..",
  "..oooo....oooo..",
 ],
}


def _with(rows, edits):
    """copy a frame and overwrite single chars: edits = [(row, col, char), ...]"""
    g = [list(r) for r in rows]
    for r, c, ch in edits: g[r][c] = ch
    return ["".join(r) for r in g]


F = HERO["front"]
# eyes are 1×2 dark pixels at columns 6 and 10 (rows 7-8); expressions only move those pixels
HERO["blink"] = _with(F, [(7, 6, "f"), (7, 10, "f"), (8, 5, "e"), (8, 7, "e"), (8, 9, "e"), (8, 11, "e")])
HERO["look_l"] = _with(F, [(7, 6, "f"), (8, 6, "f"), (7, 10, "f"), (8, 10, "f"),
                          (7, 5, "e"), (8, 5, "e"), (7, 9, "e"), (8, 9, "e")])
HERO["look_r"] = _with(F, [(7, 6, "f"), (8, 6, "f"), (7, 10, "f"), (8, 10, "f"),
                          (7, 7, "e"), (8, 7, "e"), (7, 11, "e"), (8, 11, "e"), (9, 11, "f"), (9, 10, "p")])
HERO["read"] = _with(F, [(7, 6, "f"), (7, 10, "f"), (9, 6, "e"), (9, 10, "e")])          # eyes down, reading
HERO["wow"] = _with(F, [(6, 6, "e"), (6, 10, "e"), (9, 6, "w"), (9, 10, "w")])          # big eyes: surprise

# side view, facing RIGHT (flip for left). 3-frame walk: contact A, passing, contact B
SIDE_TOP = [
  ".....oooo.......",
  "....occcco......",
  "...occcccco.....",
  "..occccccrco....",
  "..occcooooroo...",
  ".occcoffffffo...",
  ".occoffffffeo...",
  ".occoffffffeo...",
  ".occofffffpfo...",
  "..occogggggo....",
  "..oocccooooo....",
  "..occsssssso....",
  ".occckssssco....",
  "occcdcccccrco...",
  "occcdcccccrcco..",
  "occcdcccccrcco..",
  ".occdccccccrco..",
  ".oocdddddddroo..",
]
HERO["walk1"] = SIDE_TOP + [
  "..obbo...obbo...",
  ".obbo.....obbo..",
  ".ooo.......ooo..",
  "................",
]
HERO["walk2"] = SIDE_TOP + [
  "....obbobbo.....",
  "....obbobbo.....",
  "....oooooo......",
  "................",
]
HERO["walk3"] = SIDE_TOP + [
  "...obbo.obbo....",
  "..obbo...obbo...",
  "..ooo.....ooo...",
  "................",
]
for k in ("walk1", "walk2", "walk3"):           # feet sit on the last row like the front frames
    HERO[k] = ["................"] + HERO[k][:-1]

# three-quarter (turning towards RIGHT)
HERO["turn"] = [
  ".....oooo.......",
  "....occcco......",
  "...occccrco.....",
  "..occcccrcco....",
  "..occcoooocro...",
  ".occoffffforo...",
  ".occoffffffoco..",
  ".occofffefffeo..",
  ".occofffefffeo..",
  ".occoffpffffpo..",
  "..occogggggoo...",
  "..oocccoooocco..",
  ".occcssssssscco.",
  ".occckssssskco..",
  "occcdcccccccrco.",
  "occcdcccccccrco.",
  "occcdcccccccrco.",
  "occcdccccccrcco.",
  ".occdcccccccrco.",
  ".oodddddddddroo.",
  "..obbo...obbo...",
  "..oooo...oooo...",
]


def _check():
    for k, f in HERO.items():
        assert len(f) == 22 and all(len(r) == 16 for r in f), (k, len(f), [len(r) for r in f])


_check()
_LAYERS = {}


def layers(frame_rows, flip=False):
    key = (id(frame_rows), flip)
    if key not in _LAYERS:
        a = np.array([list(r) for r in frame_rows])
        if flip: a = a[:, ::-1]
        _LAYERS[key] = {ch: (a == ch) for ch in sorted(set(a.ravel()) - {"."})}
    return _LAYERS[key]


def _hex(h):
    h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def snap_colour(pal, rgb):
    """nearest exact palette colour (sprites are flat-coloured: no dither noise on a character in any palette)"""
    c = np.asarray(rgb, np.float32); return pal.colors[int(((pal.colors - c) ** 2).sum(1).argmin())]


def draw_sprite(cv, frame_rows, x, y, scale=2.0, flip=False, alpha=1.0, tint=None, squash=0.0, anchor="bottom",
                roles=None, snap=False):
    """Stamp a char-map sprite. (x, y) = bottom-centre (anchor 'bottom') or centre; scale = world units per sprite px.
    tint: a colour that replaces every role (silhouettes / ghosts). squash: >0 squashes vertically (landing).
    roles: char → '#RRGGBB' map (default: the hero's ROLES); snap: each role snaps to the nearest colour of cv.pal."""
    L = layers(frame_rows, flip); R = roles or ROLES
    h, w = len(frame_rows), len(frame_rows[0])
    sy = scale * (1 - squash); sx = scale * (1 + squash * .6)
    cy = y - h * sy / 2 if anchor == "bottom" else y
    for ch, m in L.items():
        col = tint if tint is not None else (snap_colour(cv.pal, _hex(R[ch])) if snap else _hex(R[ch]))
        if abs(sx - sy) < 1e-6:
            draw_bitmap(cv, Bitmap(m, x, cy, sx), col, alpha)
        else:   # non-uniform: resample rows
            rows = max(1, int(round(h * sy / sx)))
            idx = np.clip((np.arange(rows) * h / rows).astype(int), 0, h - 1)
            draw_bitmap(cv, Bitmap(m[idx], x, cy, sx), col, alpha)


def hero_frame(state, lb, phase=0.0):
    """Pick a hero frame for a state at local beat lb. walk: 3-frame cycle on 8ths; idle: blink every ~3.1 beats."""
    if state == "walk":
        return HERO[("walk1", "walk2", "walk3", "walk2")[int((lb + phase) * 4) % 4]]
    if state in HERO: return HERO[state]
    b = (lb + phase) % 3.1
    return HERO["blink"] if 2.95 < b < 3.1 else HERO["front"]
