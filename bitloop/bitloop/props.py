"""Diegetic brand props: the channel tag lives INSIDE the world (never a watermark).
Every prop: draw(cv, pal, t, lb, x, y, s, handle, **opt) in its layer's world coordinates; s = scale."""
import math
import numpy as np
from .bitmap import draw_text, draw_mark, text_bitmap, Bitmap, draw_bitmap
from .scenes import ease

TAU = math.pi * 2
HANDLE = "@hayret.piksel"


def _rect(cv, x, y, w, h, col, alpha=1.0):
    X, Y = cv.to_screen(x, y); b = cv._box(X, Y, cv.sl(max(w, h)) * .75 + 2)
    if b is None: return
    wx, wy = cv.world_grid()
    m = ((np.abs(wx[b] - x) <= w / 2) & (np.abs(wy[b] - y) <= h / 2)).astype(np.float32) * alpha
    cv._blend(b, m, cv._col(col))


def _frame(cv, x, y, w, h, col, th=1.2, alpha=1.0):
    for (ax, ay, bx, by) in ((x - w / 2, y - h / 2, x + w / 2, y - h / 2), (x - w / 2, y + h / 2, x + w / 2, y + h / 2),
                             (x - w / 2, y - h / 2, x - w / 2, y + h / 2), (x + w / 2, y - h / 2, x + w / 2, y + h / 2)):
        cv.line(ax, ay, bx, by, th, col, alpha)


def flicker(t, seed=0.0):
    """Neon flicker: mostly on, occasional 1–3 frame drop-outs (deterministic)."""
    u = (t * 7.3 + seed * 13.1) % 11.0
    return .15 if (2.0 < u < 2.12 or 7.4 < u < 7.48) else 1.0


def neon_sign(cv, pal, t, lb, x, y, s=1.0, handle=HANDLE, **o):
    """Shop-style neon sign on a bracket: coral tube frame, turquoise neon handle, the eye mark."""
    k = flicker(t, x)
    dot = max(1.0, round(s)); tw = (len(handle) * 6 - 1) * dot
    w, h = tw + 34 * s, 26 * s
    cv.line(x - w / 2 - 6 * s, y - h / 2 - 8 * s, x - w / 2 - 6 * s, y + h / 2, 1.5 * s, pal.ramp("bg", 1), 1)
    cv.line(x - w / 2 - 6 * s, y - h / 2 - 8 * s, x + 10 * s, y - h / 2 - 8 * s, 1.5 * s, pal.ramp("bg", 1), 1)
    _rect(cv, x, y, w, h, pal.ramp("bg", .3), .92)
    cv.glow(x, y, w * .55, pal.ramp("accent", .55), .28 * k)
    _frame(cv, x, y, w - 3 * s, h - 3 * s, pal.ramp("accent", .62 if k > .5 else .25), 1.6 * s)
    draw_mark(cv, pal, x - w / 2 + 13 * s, y, .9 * s, glow=.25 * k)
    draw_text(cv, handle, x + w / 2 - 6 * s - tw / 2, y + .5 * s, dot, pal.ramp("energy", .75 if k > .5 else .3), glow=.5 * k)


def billboard(cv, pal, t, lb, x, y, s=1.0, handle=HANDLE, **o):
    """Rooftop billboard on two legs with two lamps; big mark + two-line handle (phone-legible at s ≥ 1)."""
    w, h = 84 * s, 46 * s
    for lx in (-w / 3, w / 3):
        cv.line(x + lx, y + h / 2, x + lx, y + h / 2 + 18 * s, 2 * s, pal.ramp("bg", 1))
    _rect(cv, x, y, w + 4 * s, h + 4 * s, pal.ramp("bg", .9), 1)
    _rect(cv, x, y, w, h, pal.ramp("body", .18), 1)
    for lx in (-w / 3, w / 3):
        cv.disc(x + lx, y + h / 2 + 3 * s, 1.5 * s, pal.ramp("pale", 1)); cv.glow(x + lx, y + h / 4, 18 * s, pal.ramp("pale", .8), .18)
    draw_mark(cv, pal, x - w / 2 + 16 * s, y, 1.4 * s, glow=.3)
    draw_text(cv, "@hayret\n.piksel", x + 13 * s, y, max(1.0, round(s)), pal.ramp("pale", 1))
    sweep = ((t * .4) % 1.6) - .3
    if 0 <= sweep <= 1:
        cv.line(x - w / 2 + sweep * w, y - h / 2, x - w / 2 + sweep * w - 8 * s, y + h / 2, 2 * s, pal.ramp("pale", 1), .18)


def _snap_k(dot, zoom):
    """art px per font dot as bitmap.draw_bitmap(snap=True) will stamp it."""
    return max(1, int(round(dot * zoom))) if dot * zoom < 1.75 else dot * zoom


def hive_label(cv, pal, t, lb, x, y, s=1.0, handle=HANDLE, model="", **o):
    """Painted wooden label nailed on a beehive: cream planks, dark painted two-line handle, small model line.
    Sized from the SNAPPED text so the board always fits the letters at any camera zoom (≥ 6 output px per dot)."""
    from .minifont import mini_bitmap, draw_mini
    z = cv.cam.zoom; dot = max(1.0, round(s * .75))
    txt = handle.replace(".", "\n.", 1) if len(handle) > 9 and "." in handle else handle
    bm = text_bitmap(txt); k = _snap_k(dot, z)
    tw, th = bm.shape[1] * k / z, bm.shape[0] * k / z
    mb = mini_bitmap(model) if model else np.zeros((0, 0), bool); km = _snap_k(1.0, z)
    mw, mh = mb.shape[1] * km / z, mb.shape[0] * km / z
    w = max(tw, mw) + 8 / z * max(1, k); h = th + (mh + 3 / z if model else 0) + 6 / z * max(1, k)
    wood, grain, ink = (.95, .91, .82), (.74, .64, .50), (.08, .06, .07)       # cream paint on wood, near-black letters
    _rect(cv, x + .8, y + 1.2, w, h, (.20, .13, .08), .9)                         # shadow on the hive
    _rect(cv, x, y, w, h, wood, 1)
    for j in range(1, 3):                                                          # plank seams
        yy = y - h / 2 + h * j / 3; cv.line(x - w / 2, yy, x + w / 2, yy, .5, grain, .55)
    for sx in (-1, 1):
        for sy in (-1, 1): cv.disc(x + sx * (w / 2 - 1.6), y + sy * (h / 2 - 1.6), .7, (.35, .36, .38))
    cv.matte(x, y, w, h, .9)
    ty = y - h / 2 + 3 / z * max(1, k) + th / 2
    draw_text(cv, txt, x, ty, dot, ink, snap=True)
    if model: draw_mini(cv, model, x, ty + th / 2 + 2.5 / z + mh / 2, 1.0, (.55, .22, .12), snap=True)


def plate(cv, pal, t, lb, x, y, s=1.0, handle=HANDLE, model="MK-II", **o):
    """Engraved metal brand plate with screws (lab equipment, machines). skin="hive": painted wooden hive label."""
    if o.get("skin") == "hive": return hive_label(cv, pal, t, lb, x, y, s, handle, model, **o)
    w, h = 92 * s, 22 * s
    _rect(cv, x, y + 1.5 * s, w, h, pal.ramp("bg", .2), .9)
    w = max(w, (len(handle) * 6 - 1) * max(1.0, round(s * .9)) + 34 * s)
    _rect(cv, x, y, w, h, pal.ramp("pale", .82), 1)
    _frame(cv, x, y, w - 3 * s, h - 3 * s, pal.ramp("pale", .45), 1)
    for sx in (-1, 1):
        for sy in (-1, 1): cv.disc(x + sx * (w / 2 - 4 * s), y + sy * (h / 2 - 4 * s), 1.1 * s, pal.ramp("pale", .2))
    draw_mark(cv, pal, x - w / 2 + 13 * s, y, .8 * s, glow=0, mono=pal.ramp("bg", .3), snap=True)
    cv.matte(x, y, w, h, .9)                                          # engraved metal: no bloom over the engraving
    draw_text(cv, handle, x + 9 * s, y - 3.5 * s, max(1.0, round(s * .9)), pal.ramp("bg", .3), snap=True)
    draw_text(cv, model, x + 7 * s, y + 5.5 * s, max(1.0, round(s * .9)), pal.ramp("accent", .12), snap=True)
    sh = ((t * .5) % 2.0) - .5
    if 0 < sh < 1: cv.line(x - w / 2 + sh * w, y - h / 2, x - w / 2 + sh * w + 5 * s, y + h / 2, 3 * s, pal.ramp("pale", 1), .35)


def patch(cv, pal, t, lb, x, y, s=1.0, handle=HANDLE, **o):
    """Mission patch: coral-rimmed cobalt disc with the eye mark and a ribbon with the handle."""
    r = 22 * s
    cv.disc(x, y, r + 2 * s, pal.ramp("accent", .55)); cv.disc(x, y, r, pal.ramp("body", .3))
    cv.ring(x, y, r - 3 * s, 1, pal.ramp("pale", .8), .8, dashes=16, phase=t * .05)
    draw_mark(cv, pal, x, y - 2 * s, 1.0 * s, glow=.2)
    bw = 92 * s
    _rect(cv, x, y + r, bw, 13 * s, pal.ramp("accent", .3), 1)
    for sx in (-1, 1): cv.line(x + sx * bw / 2, y + r - 6 * s, x + sx * (bw / 2 + 5 * s), y + r + 6 * s, 2 * s, pal.ramp("accent", .2))
    draw_text(cv, handle, x, y + r + .5 * s, max(1.0, round(s * .9)), pal.ramp("pale", 1))


def ship(cv, pal, t, lb, x, y, s=1.0, handle=HANDLE, speed=14.0, **o):
    """A small spacecraft crossing the frame, handle painted on its hull, engine trail in turquoise."""
    span = o.get("span", 260.0)
    X = x + ((t * speed * s) % span) - span / 2 if o.get("moving", True) else x
    Y = y + math.sin(t * .8) * 2 * s
    L = max(110 * s, (len(handle) * 6 - 1) * max(1.0, round(s)) + 46 * s)
    for i in range(14):
        cv.disc(X - L / 2 - i * 4 * s, Y + (i % 2) * .5, (3.5 - i * .22) * s, pal.ramp("energy", .9 - i * .05), .6 * (1 - i / 14))
    cv.glow(X - L / 2 - 2 * s, Y, 8 * s, pal.ramp("energy", .8), .7)
    cv.capsule(X - L / 2, Y, X + L / 2 - 8 * s, Y, 9 * s, ramp="pale")
    cv.capsule(X + L / 2 - 14 * s, Y - 1 * s, X + L / 2, Y + 1 * s, 6 * s, ramp="pale")
    cv.capsule(X - L / 4, Y - 10 * s, X - L / 4 + 20 * s, Y - 12 * s, 2.5 * s, ramp="body")
    cv.capsule(X - L / 4, Y + 10 * s, X - L / 4 + 20 * s, Y + 12 * s, 2.5 * s, ramp="body")
    for i in range(3):
        on = (t * 2 + i * .3) % 1.0 < .6
        cv.disc(X + L / 2 - 12 * s, Y - 3 * s + i * 3 * s, .9 * s, pal.ramp("energy" if on else "body", .8))
    draw_mark(cv, pal, X - L / 2 + 13 * s, Y, .55 * s, glow=0)
    cv.capsule(X - L / 2 + 22 * s, Y + 4 * s, X + L / 2 - 18 * s, Y + 4 * s, 1.2 * s, flat=pal.ramp("accent", .45))
    draw_text(cv, handle, X + 2 * s, Y - 2 * s, max(1.0, round(s)), pal.ramp("bg", .45))
    k = 1.0 if (t * 1.5) % 1.0 < .15 else 0.0
    cv.disc(X + L / 2 - 4 * s, Y - 7 * s, 1 * s, pal.ramp("accent", .6), k)


def terminal(cv, pal, t, lb, x, y, s=1.0, handle=HANDLE, lines=None, **o):
    """CRT monitor with boot text typing out (handle in the boot line), blinking cursor, scanlines."""
    lines = lines or [f"> {handle}", "> merak.exe", "> yükleniyor", "> HAYRET!"]
    dot = max(1.0, round(s * .8))
    w, h = max(96 * s, max(len(l) for l in lines) * 6 * dot + 14 * s), 70 * s    # widen to fit the longest line
    _rect(cv, x, y + h / 2 + 8 * s, 30 * s, 10 * s, pal.ramp("pale", .35), 1)
    _rect(cv, x, y, w + 10 * s, h + 10 * s, pal.ramp("pale", .45), 1)
    _rect(cv, x, y, w, h, pal.ramp("bg", .25), 1)
    cv.glow(x, y, w * .45, pal.ramp("energy", .5), .2)
    shown = int(max(0.0, (t - o.get("start", 0.0))) * 16)
    yy = y - h / 2 + 9 * s
    for i, l in enumerate(lines):
        n = max(0, min(len(l), shown)); shown -= len(l) + 3
        if n: draw_text(cv, l[:n], x - w / 2 + 6 * s + (n * 6 - 1) * max(1.0, round(s * .8)) / 2, yy, max(1.0, round(s * .8)),
                        pal.ramp("energy" if i != 3 else "accent", .75 if i != 3 else .6), snap=True)
        if 0 < n < len(l) or (n == len(l) and shown < 0 and i == len(lines) - 1):
            if (t * 2) % 1 < .55: _rect(cv, x - w / 2 + 6 * s + n * 6 * max(1.0, round(s * .8)) + 3 * s, yy, 4 * s, 7 * s, pal.ramp("energy", .8))
        yy += 13 * s
        if shown < 0: break
    for k in range(int(h / (3 * s))):
        cv.line(x - w / 2, y - h / 2 + k * 3 * s, x + w / 2, y - h / 2 + k * 3 * s, .5, pal.ramp("bg", 0), .25)
    cv.disc(x + w / 2 - 2 * s, y + h / 2 + 3 * s, 1 * s, pal.ramp("energy", .8))


def _slate(pal):
    """board fill: the palette's own 'board' ramp when it has one (kara_tahta), else the legacy energy(.08)"""
    return pal.ramp("board", .5) if "board" in pal.ramps else pal.ramp("energy", .08)


def chalkboard(cv, pal, t, lb, x, y, s=1.0, handle=HANDLE, doodle=True, lines=None, **o):
    """Framed classroom board corner: chalk handle + chalk eye doodle + a chalk formula squiggle.
    lines=[...]: write these lines in chalk instead of the squiggle (formulas); the handle stays small in the corner."""
    if lines:
        from .bitmap import text_bitmap
        tw = max(text_bitmap(l).shape[1] for l in lines); w = max(100 * s, tw + 14); h = 13 * len(lines) + 22
        _rect(cv, x, y, w + 8, h + 8, pal.ramp("accent", .12), 1)
        _rect(cv, x, y, w, h, _slate(pal), 1)
        chalk = pal.ramp("pale", .85)
        for i, l in enumerate(lines):
            n = int(max(0.0, t * 18 - i * 14))                           # chalk writes itself
            if n > 0: draw_text(cv, l[:n], x - w / 2 + 7 + (min(n, len(l)) * 6 - 1) / 2, y - h / 2 + 9 + i * 13, 1, chalk, alpha=.92)
        from .minifont import draw_mini
        draw_text(cv, handle, x + w / 2 - 4 - (len(handle) * 6 - 1) / 2, y + h / 2 - 7, 1, pal.ramp("pale", .6), alpha=.75)
        if doodle: draw_mark(cv, pal, x + w / 2 - 12, y - h / 2 + 9, .6, glow=0, mono=pal.ramp("pale", .7))
        _rect(cv, x - w / 2 + 14, y + h / 2 + 2, 12, 3, pal.ramp("pale", 1), 1)
        return
    w, h = 100 * s, 64 * s
    _rect(cv, x, y, w + 8 * s, h + 8 * s, pal.ramp("accent", .12), 1)
    _rect(cv, x, y, w, h, _slate(pal), 1)
    chalk = pal.ramp("pale", .85)
    draw_text(cv, handle, x, y + h / 2 - 12 * s, max(1.0, round(s)), chalk, alpha=.9)
    if doodle: draw_mark(cv, pal, x - 22 * s, y - 8 * s, 1.0 * s, glow=0, mono=chalk)
    pts = [(x + 2 * s + i * 4 * s, y - 10 * s + 3 * s * math.sin(i * 1.3)) for i in range(9)]
    cv.polyline(pts, .6, flat=chalk, alpha=.7)
    draw_text(cv, "=?!", x + 24 * s, y + 2 * s, max(1.0, round(s)), pal.ramp("accent", .6))
    _rect(cv, x + w / 2 - 14 * s, y + h / 2 + 2 * s, 12 * s, 3 * s, pal.ramp("pale", 1), 1)


def stamp(cv, pal, t, lb, x, y, s=1.0, handle=HANDLE, at=0.0, rot=-12, **o):
    """Rubber stamp 'HAYRET!' + handle that thunks in on beat `at` (scale pop), coral ink, slight rotation."""
    if lb < at: return
    k = ease(min(1.0, (lb - at) / .25), "outCubic"); sc = s * (1.5 - .5 * k)
    ink = pal.ramp("accent", .45); a = .9 * min(1.0, (lb - at) / .1)
    r = max(30 * sc, (len(handle) * 6 - 1) * max(1.0, round(sc * .8)) / 2 + 6 * sc)
    cv.ring(x, y, r, 2.4 * sc, ink, a); cv.ring(x, y, r - 4 * sc, 1 * sc, ink, a)
    rr = math.radians(rot)
    draw_text(cv, "HAYRET!", x + 7 * sc * math.sin(rr), y - 7 * sc * math.cos(rr), max(1.0, round(sc * 1.2)), ink, alpha=a, rot=rot)
    draw_text(cv, handle, x - 8 * sc * math.sin(rr), y + 8 * sc * math.cos(rr), max(1.0, round(sc * .8)), ink, alpha=a, rot=rot)


PROPS = {"neon_sign": neon_sign, "billboard": billboard, "plate": plate, "patch": patch, "ship": ship,
         "terminal": terminal, "chalkboard": chalkboard, "stamp": stamp}
