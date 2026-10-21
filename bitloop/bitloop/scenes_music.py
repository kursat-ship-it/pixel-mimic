"""Music / notation scenes (reusable, topic-agnostic): a self-similar scrolling staff driven by an integer series on the
GLOBAL beat grid (so lit notes = audible notes, by construction), a CRT noise oscilloscope (white / pink 1/f / brown),
a growing binary tree of a recursive series, and a Shepard (endless) staircase of piano keys.
All draw in world units (≈ art px at zoom 1, origin = frame centre, y down) as pure functions of time."""
import math
import numpy as np
from .scenes import Scene, ease, pulse, TAU
from .theory import series_value, series_index
from .minifont import draw_mini
from .bitmap import Bitmap, draw_bitmap


def _sprite(rows):
    return np.array([[c == "#" for c in r] for r in rows])


TREBLE = _sprite([
    ".....##..", "....#..#.", "....#..#.", "....#.#..", "....##...", "...##....", "..#.#....", ".#..#....",
    "#...####.", "#..#.#..#", "#..#..#.#", ".#..#.#.#", "..####.#.", "......#..", "......#..", "..##..#..",
    "..##..#..", "...###...",
])
BASS = _sprite([".###..#", "#...#..", "....#.#", "...#...", "..#....", "##....."])
FLAT = _sprite(["#..", "#..", "###", "#.#", "##."])
SHARP = _sprite([".#.#", "####", ".#.#", "####", ".#.#"])
EIGHTH = _sprite([".#..", ".##.", ".#.#", ".#..", "##..", "##.."])          # ♪ glyph for emitters / sprites


class FractalStaff(Scene):
    """A 5-line pixel staff whose notes are an integer series (default Nørgård) scrolling right→left past a playhead.
    Note n sits at x = playhead + (n − beat·rate)·spacing and lights on its exact onset floor(beat·rate) = n — the same
    formula the music engine uses (theory.series_index), so picture and sound cannot drift.
    modes: play (scroll + light) · nest (note heads contain scaled copies of the staff, recursion to `depth`, LOD-limited)
    · every4 (every `every`-th note burns, the rest dim; at drop_to_bass_at the lit notes fall onto a bass staff that
    shows the series `every`× slower = the same contour; later both light together on shared onsets).
    Extras: ghost (list of k: faint k× bigger staves playing the series k× slower behind, aligned on the playhead),
    zoom_into_note (series index the camera crash-zooms into; focus follows it), nest_preview (that head pops open
    with a staff inside at nest_at), show_parent_edge (enter from inside a giant head), from_groove (lines start as record
    grooves straightening), converge_to_frame0 (end state = film frame 0: wraps the series at the loop length)."""
    defaults = {"mode": "play", "series": "norgard", "rate": 4, "sign": 1, "depth": 0, "playhead": True,
                "playhead_x": -20.0, "spacing": 10.0, "y": 0.0, "gap": 7.0, "x0": -86.0, "head": 1.15, "zoom_into_note": None,
                "nest_preview": False, "nest_at": 4.0, "nest_scale": 3.4, "bass_staff": False, "bass_gap": 50.0,
                "bass_in": 0.0, "show_parent_edge": False, "parent_beats": 1.5, "dim_others": False, "every": 4,
                "solo_until": 4.0, "drop_to_bass_at": None, "fall_beats": .75, "fall_stagger": .125,
                "converge_to_frame0": False, "from_groove": False, "groove_beats": 1.25, "ghost": [4, 16], "ghost_alpha": .22, "key_sig": -1,
                "period": None, "sparks": True, "keys": False, "keys_y": 62.0, "keys_scale": "dorian", "keys_bass": True}

    def setup(self):
        self.hx, self.hy = 2.7 * self.p["head"], 2.0 * self.p["head"]; self.stx = self.hx * .82

    def on_bind(self):
        p = self.p
        self.period = p["period"] or (int(round(self.total * p["rate"])) if self.loop and self.total else None)

    # ------------------------------------------------------------------ series helpers
    def val(self, n, rate):
        per = None
        if self.period: per = max(1, int(round(self.period * rate / self.p["rate"])))
        idx = np.mod(n, per) if per else np.maximum(n, 0)
        return self.p["sign"] * series_value(self.p["series"], idx)

    def note_x(self, n, gb, rate, sp):
        return self.p["playhead_x"] + (n - gb * rate) * sp

    def _head_y(self, d, base, gap, bass=False):
        pos = d + (0 if bass else 2)                       # staff position (0 = bottom line): treble G4 / bass G2 = 2nd line
        return base + 2 * gap - pos * gap / 2, pos

    def target_pos(self, lb):
        n = self.p["zoom_into_note"]
        if n is None: return (self.p["playhead_x"], self.p["y"])
        gb = self.gbeat(lb); d = int(self.val(np.array([n]), self.p["rate"])[0])
        y, _ = self._head_y(d, self.p["y"], self.p["gap"])
        return (self.note_x(n, gb, self.p["rate"], self.p["spacing"]), y)

    def focus(self, lb, dur_b):
        return self.target_pos(lb)

    # ------------------------------------------------------------------ drawing primitives in a (possibly nested) frame
    def _lines(self, cv, T, xa, xb, base, gap, col, alpha, clip=None, warp=None):
        ox, oy, s = T
        for k in range(5):
            y = base + k * gap
            if warp is not None:
                xs = np.linspace(xa, xb, 90); pts = [(ox + s * x, oy + s * (y + warp(x, y))) for x in xs]
                cv.poly_outline(pts, col, alpha, width=max(1, int(round(cv.cam.zoom * min(s, 1.6) * .8))), closed=False); continue
            x1, x2 = xa, xb
            if clip is not None:
                cx, cy, rx, ry = clip; wy = oy + s * y
                q = 1 - ((wy - cy) / ry) ** 2
                if q <= 0: continue
                hw = rx * math.sqrt(q); x1 = max(xa, (cx - hw - ox) / s); x2 = min(xb, (cx + hw - ox) / s)
                if x2 <= x1: continue
            cv.poly_outline([(ox + s * x1, oy + s * y), (ox + s * x2, oy + s * y)], col, alpha,
                            width=max(1, int(round(cv.cam.zoom * min(s, 1.6) * .8))), closed=False)

    def _staff(self, cv, T, gb, lb, level, clip=None, rate=None, base=None, bass=False, alpha=1.0, warp=None,
               note_alpha=1.0, mode=None, every_dim=0.0, solo=False, hide=None, lit_boost=1.0, sp=None):
        """Draw one staff (lines, clef, key signature, beamed notes, lit notes) in frame T=(ox,oy,s)."""
        p, E, pal = self.p, self.E, self.pal
        ox, oy, s = T; rate = rate or p["rate"]; gap = p["gap"]; base = p["y"] - 2 * gap if base is None else base
        sp = sp or p["spacing"] * p["rate"] / rate           # bass notes: spaced `every`× wider, same scroll speed
        z = cv.cam.zoom * s                                  # screen px per local unit
        if z * gap < .9: return []
        R = math.hypot(cv.W, cv.H) / 2 / cv.cam.zoom + 12
        xa = max(p["x0"], (cv.cam.cx - R - ox) / s); xb = (cv.cam.cx + R - ox) / s
        if clip is not None:
            cx, cy, rx, ry = clip; xa = max(xa, (cx - rx - ox) / s); xb = min(xb, (cx + rx - ox) / s)
        if xb <= xa: return []
        wy = lambda x, y: y + (warp(x, y) if warp else 0.0)
        line_col = pal.ramp("pale", .82 if level == 0 else .7)
        self._lines(cv, T, xa, xb, base, gap, line_col, .9 * alpha, clip, warp)
        heads = []
        if z * gap < 2.2: return heads                      # LOD: lines only
        # clef + key signature at the staff start
        if clip is None and xa <= p["x0"] + 1:
            spr = BASS if bass else TREBLE
            cy_ = base + (gap * .9 if bass else gap * 2.1)
            hgt = gap * (1.6 if bass else 5.6)
            bx, by, bs = ox + s * (p["x0"] + 5), oy + s * wy(p["x0"] + 5, cy_), hgt * s / spr.shape[0]
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):       # ink outline: keeps the clef legible on any nebula
                draw_bitmap(cv, Bitmap(spr, bx + dx / cv.cam.zoom, by + dy / cv.cam.zoom, bs), pal.ramp("bg", .05), alpha)
            draw_bitmap(cv, Bitmap(spr, bx, by, bs), pal.ramp("pale", .95), alpha)
            cv.line(ox + s * p["x0"], oy + s * wy(p["x0"], base), ox + s * p["x0"], oy + s * wy(p["x0"], base + 4 * gap),
                    max(.8, 1.0 * s), pal.ramp("pale", .9), alpha)
            ks = p["key_sig"]
            for i in range(abs(int(ks))):
                if ks < 0:   # flats B E A … (treble: B4 = middle line; bass: B2 = 2nd line)
                    pos = [4, 7, 3][i] if not bass else [2, 5, 1][i]; spr2 = FLAT; yy = base + 4 * gap - pos * gap / 2 - gap * .35
                else:        # sharps F C …
                    pos = [8, 5, 9][i] if not bass else [6, 3, 7][i]; spr2 = SHARP; yy = base + 4 * gap - pos * gap / 2
                xx = p["x0"] + 13 + i * 4
                draw_bitmap(cv, Bitmap(spr2, ox + s * xx, oy + s * wy(xx, yy), s * gap * .9 / 5), pal.ramp("pale", .9), alpha)
        x_start = p["x0"] + 16 + 4 * abs(int(p["key_sig"]))
        gbr = gb * rate
        n_lo = int(math.floor(gbr + (max(xa, x_start) - p["playhead_x"]) / sp)) - 1
        n_hi = int(math.ceil(gbr + (xb - p["playhead_x"]) / sp)) + 1
        if n_hi - n_lo > 220: n_hi = n_lo + 220
        ns = np.arange(n_lo, n_hi + 1)
        vals = self.val(ns, rate)
        group = {4: 4, 2: 2}.get(int(rate), 1) if rate >= 2 else 1
        nbeams = {4: 2, 2: 1}.get(int(rate), 0)
        info = []
        for n, d in zip(ns, vals):
            x = self.note_x(n, gb, rate, sp)
            if x < x_start - 3 or x > xb + 4: continue
            y0, pos = self._head_y(int(d), base, gap, bass)
            since = gbr - n                                       # 16ths (or this staff's units) since onset
            fade_l = float(np.clip((x - x_start) / 8, 0, 1))
            if hide is not None and hide(n): continue
            info.append((n, x, y0, pos, since, fade_l))
        # beams / stems per group
        lit_col = E(.95); fut = pal.ramp("pale", .72); past = pal.ramp("body", .52); dimc = pal.ramp("bg", .9)
        for gi in sorted(set(int(math.floor(n / group)) for n, *_ in info)):
            grp = [t for t in info if int(math.floor(t[0] / group)) == gi]
            up = np.mean([t[3] for t in grp]) < 4
            for n, x, y0, pos, since, fl in grp:
                a = fl * note_alpha * alpha
                dm = every_dim if (mode == "every4" and n % p["every"] != 0) else 0.0
                c = fut if since < 0 else past
                if dm: c = c * (1 - dm) + dimc * dm; a *= 1 - .7 * dm
                stx = x + (self.stx if up else -self.stx)
                if group == 1 or len(grp) == 1:
                    cv.line(ox + s * stx, oy + s * wy(stx, y0), ox + s * stx, oy + s * wy(stx, y0 + (-2.6 if up else 2.6) * gap), max(.7, .9 * s), c, a)
            if group > 1 and len(grp) > 1:
                ys = [t[2] for t in grp]; bx0, bx1 = grp[0][1], grp[-1][1]
                by = (min(ys) - 2.4 * gap) if up else (max(ys) + 2.4 * gap)
                sl = float(np.clip((grp[-1][2] - grp[0][2]) * .25, -3, 3))
                for n, x, y0, pos, since, fl in grp:
                    dm = every_dim if (mode == "every4" and n % p["every"] != 0) else 0.0
                    c = (fut if since < 0 else past); a = fl * note_alpha * alpha * (1 - .7 * dm)
                    if dm: c = c * (1 - dm) + dimc * dm
                    stx = x + (self.stx if up else -self.stx); k = (x - bx0) / max(bx1 - bx0, 1e-6)
                    cv.line(ox + s * stx, oy + s * wy(stx, y0), ox + s * stx, oy + s * wy(stx, by + sl * k), max(.7, .9 * s), c, a)
                gdim = every_dim if mode == "every4" else 0.0
                cb = (fut if grp[0][4] < 0 else past); cb = cb * (1 - gdim * .8) + dimc * gdim * .8
                ab = min(t[5] for t in grp) * note_alpha * alpha * (1 - .5 * gdim)
                xa_ = bx0 + (self.stx if up else -self.stx); xb_ = bx1 + (self.stx if up else -self.stx)
                for bi in range(nbeams):
                    off = bi * .5 * gap * (1 if up else -1)
                    cv.line(ox + s * xa_, oy + s * wy(xa_, by + off), ox + s * xb_, oy + s * wy(xb_, by + sl + off), max(1.0, 1.7 * s), cb, ab)
        # ledger lines + heads (+ lit glow, echo trail)
        for n, x, y0, pos, since, fl in info:
            dm = every_dim if (mode == "every4" and n % p["every"] != 0) else 0.0
            a = fl * note_alpha * alpha * (1 - .7 * dm)
            for lp in list(range(-2, pos - 1, -2)) + list(range(10, pos + 1, 2)):
                ly = base + 4 * gap - lp * gap / 2
                cv.line(ox + s * (x - 4), oy + s * wy(x, ly), ox + s * (x + 4), oy + s * wy(x, ly), max(.7, .9 * s), line_col, .9 * a)
            sounding = not (solo and n % p["every"] != 0)
            lit = 0.0
            if sounding and since >= 0:
                lit = 1.0 if since < 1 else math.exp(-(since - 1) * .9)
            burn = 1.0 if (mode == "every4" and n % p["every"] == 0 and every_dim > 0) else 0.0
            c = fut if since < 0 else past
            if dm: c = c * (1 - dm) + dimc * dm
            if burn: c = c * (1 - .75 * burn) + E(.72) * .75 * burn
            c = c * (1 - lit) + lit_col * lit
            hx, hy = ox + s * x, oy + s * wy(x, y0)
            if lit > .05 and level == 0:
                cv.glow(hx, hy, 6 * s * (1 + .4 * lit_boost), E(.62), .42 * lit * a * lit_boost)
                for j, k in enumerate((.5, .3, .15)):           # echo trail (where the note came from)
                    if since < 3: cv.disc(hx + s * (3.5 + 3.2 * j), hy, max(.5, .9 * s), E(.8), k * lit * a)
            if burn and level == 0: cv.glow(hx, hy, 5 * s, E(.7), .35 * a)
            cv.ellipse(hx, hy, self.hx * s, self.hy * s, c, a, ang=-.35)
            if s * cv.cam.zoom >= 1.5 and lit < .5:
                cv.ellipse(hx - .7 * s, hy - .5 * s, .9 * s, .5 * s, pal.ramp("pale", 1.0), .55 * a, ang=-.35)
            heads.append((n, hx, hy, lit, since, a))
        return heads

    # ------------------------------------------------------------------ nesting
    def _nest(self, cv, gb, lb, hx, hy, rx, ry, level, depth, fill_col, alpha=1.0):
        """Draw a scaled copy of the staff inside a note head (clip ellipse) — recursion to `depth`, LOD-limited."""
        cv.ellipse(hx, hy, rx, ry, fill_col, alpha, ang=0)
        s = ry * 1.15 / (4 * self.p["gap"])
        if cv.sl(ry) < 3.5: return
        T = (hx - s * (self.p["playhead_x"] + 20), hy - s * self.p["y"], s)
        heads = self._staff(cv, T, gb, lb, level, clip=(hx, hy, rx * .92, ry * .92), alpha=alpha)
        if cv.sl(rx) > 9:   # a mini playhead in the head
            cv.line(T[0] + s * self.p["playhead_x"], hy - ry * .7, T[0] + s * self.p["playhead_x"], hy + ry * .7, max(.5, s), self.E(.7), .6 * alpha)
        if level < depth:
            for n, x, y, lit, since, a in heads:
                if cv.sl(self.hy * s) > 6: self._nest(cv, gb, lb, x, y, self.hx * s, self.hy * s, level + 1, depth, self.pal.ramp("bg", .2), a)

    # ------------------------------------------------------------------ main
    def draw(self, cv, lt, lb, dur_b):
        p, E, pal = self.p, self.E, self.pal
        gb = self.gbeat(lb); mode = p["mode"]
        warp = None; note_alpha = 1.0
        if p["from_groove"] and lb < p["groove_beats"]:
            e = ease(max(lb, 0) / p["groove_beats"], "outCubic")
            Rg = 34 + 3000 * e ** 3
            cyc = p["y"] + Rg
            def warp(x, y, Rg=Rg, cyc=cyc):
                r = cyc - y; q = r * r - x * x
                return (r - math.sqrt(q)) if q > 0 else r
            note_alpha = float(np.clip((e - .45) / .4, 0, 1))
            for k in range(1, 9):     # leftover grooves around the opened ones (fade as they straighten)
                rr = Rg - 2 * p["gap"] - 30 - k * 5
                if rr > 4: cv.ring(0, cyc, rr, .8, pal.ramp("dim", .7), .5 * (1 - e))
        # ghost staves: the same series k× slower and k× bigger (the "melody inside the melody")
        for k in (p["ghost"] or []):
            gT = (p["playhead_x"] * (1 - k), p["y"] * (1 - k), float(k))
            self._staff(cv, gT, gb, lb, 1, rate=p["rate"] / k, alpha=p["ghost_alpha"] * (4 / k) ** .35 * (1.3 if mode == "nest" else 1.0), warp=None,
                        note_alpha=1.0, sp=p["spacing"])
        # every4 timing
        dim = 0.0; solo = False
        if mode == "every4":
            dim = ease(min(1, max(0, lb) / .5)) if p["dim_others"] else 0.0
            if lb >= p["solo_until"]: dim *= 1 - ease(min(1, (lb - p["solo_until"]) / .5))
            solo = lb < p["solo_until"]
        heads = self._staff(cv, (0, 0, 1.0), gb, lb, 0, warp=warp, note_alpha=note_alpha, mode=mode, every_dim=dim, solo=solo)
        # bass staff (series every× slower, same scroll speed → aligned under every every-th note)
        bheads = []
        if p["bass_staff"]:
            ev = p["every"]; base = p["y"] + p["bass_gap"] - 2 * p["gap"]
            ka = ease(min(1, max(0, lb - p["bass_in"]) / .75))
            hide = None
            if mode == "every4" and p["drop_to_bass_at"] is not None:
                n_first, landed_at = self._fall_plan(lb)
                hide = lambda n: lb < landed_at(n)
            bheads = self._staff(cv, (0, 0, 1.0), gb, lb, 0, rate=p["rate"] / ev, base=base, bass=True, alpha=ka, hide=hide)
            if mode == "every4" and p["drop_to_bass_at"] is not None:
                self._draw_falls(cv, gb, lb, base)
        # piano keyboard (fills the lower third): the key of the note under the playhead lights on its exact onset
        if p["keys"]: self._keys(cv, gb, lb, note_alpha)
        # playhead
        if p["playhead"]:
            ph = p["playhead_x"]; top = p["y"] - 30; bot = p["y"] + (p["bass_gap"] + 22 if p["bass_staff"] else 26)
            q = pulse(gb * p["rate"], 1.0, 5.0)
            cv.line(ph, top, ph, bot, 1.0, E(.55), .55 * note_alpha)
            cv.glow(ph, p["y"], 9, E(.6), (.18 + .12 * q) * note_alpha)
            for yy in (top, bot): cv.disc(ph, yy, 1.4, E(.9), .9 * note_alpha)
        # unison sparks (top note k·every and bass note k light together)
        if p["bass_staff"] and bheads and (mode != "every4" or lb >= p["solo_until"] - 1e-6 or True):
            for n, hx, hy, lit, since, a in bheads:
                if 0 <= since < .5 and a > .5:
                    top_y = next((h[2] for h in heads if h[0] == n * p["every"]), None)
                    if top_y is None: continue
                    k = 1 - since / .5
                    for j in range(6):
                        yy = top_y + (hy - top_y) * (j + .5) / 6
                        cv.disc(hx + (1.2 if j % 2 else -1.2) * k, yy, .7, E(1.0), .9 * k)
                    cv.glow(hx, (top_y + hy) / 2, 10, E(.9), .5 * k)
        # sound sparks rising off the lit note
        if p["sparks"]:
            for n, hx, hy, lit, since, a in heads:
                if 0 <= since < 2.5 and lit > .1:
                    for j in range(3):
                        u = since / 2.5; r = ((n * 7 + j * 13) % 11) / 11 - .5
                        cv.points([hx + r * 8 + j - 1], [hy - 4 - u * 14 - j * 3], E(.9 if j else 1.0), alpha=(1 - u) * a)
        # nest: heads contain the staff again
        depth = int(p["depth"])
        if mode == "nest" and depth > 0:
            for n, hx, hy, lit, since, a in heads:
                if cv.sl(2.0) > 5: self._nest(cv, gb, lb, hx, hy, self.hx * .9, self.hy * .9, 1, depth, pal.ramp("bg", .25), a)
        # the target note pops open (S1 hook) → camera crash-zooms into it
        if p["nest_preview"] and p["zoom_into_note"] is not None and lb >= p["nest_at"] - .02:
            k = ease(min(1, (lb - p["nest_at"]) / .35), "outCubic"); ov = 1 + .25 * math.sin(min(1, (lb - p["nest_at"]) / .5) * math.pi)
            tx, ty = self.target_pos(lb); sc = 1 + (p["nest_scale"] - 1) * k * ov
            rx, ry = self.hx * sc, self.hy * sc
            cv.glow(tx, ty, 10 * sc / 2, E(.9), .6)
            cv.ellipse(tx, ty, rx + .9, ry + .9, E(.95), 1.0)
            self._nest(cv, gb, lb, tx, ty, rx, ry, 1, max(1, depth + 1), pal.ramp("bg", .1))
            cv.ring(tx, ty, max(rx, ry) + 2 + 6 * (1 - k), .7, E(1.0), .8 * (1 - k))
        if p["show_parent_edge"] and lb < p["parent_beats"]:
            self._parent_edge(cv, lb)

    _SCALES = {"dorian": [0, 2, 3, 5, 7, 9, 10], "lydian": [0, 2, 4, 6, 7, 9, 11], "major": [0, 2, 4, 5, 7, 9, 11],
               "minor": [0, 2, 3, 5, 7, 8, 10], "mixolydian": [0, 2, 4, 5, 7, 9, 10], "phrygian": [0, 1, 3, 5, 7, 8, 10]}

    def _keys(self, cv, gb, lb, fade=1.0):
        """A pixel piano (2 octaves + a 2nd, from the key root −1 oct): white keys cream with lapis shading, black keys
        gece. The lead note (series at `rate`) lights its key turquoise on its onset and decays over a 16th; with
        keys_bass the slow copy (rate/every) marks its key with a coral pip, so 'every 4th note = same melody' is
        visible on the keys too. Pure function of the global beat (seam-safe)."""
        p, E, A, pal = self.p, self.E, self.A, self.pal
        iv = self._SCALES.get(p["keys_scale"], self._SCALES["dorian"])
        semi = lambda d: 12 * (d // 7) + iv[d % 7]
        WHITE = {0, 2, 4, 5, 7, 9, 10}            # semitones above G that are white keys (G A B C D E F)
        lo, hi = -12, 14
        whites = [k for k in range(lo, hi + 1) if (k % 12) in WHITE]
        kw = 168.0 / len(whites); x_l = -84.0; y0 = p["keys_y"]; hW, hB = 22.0, 13.0
        xpos = {k: x_l + (i + .5) * kw for i, k in enumerate(whites)}
        a = fade
        # lit state
        rate = p["rate"]; n = int(math.floor(gb * rate + 1e-9)); since = gb * rate - n
        lead_k = semi(int(self.val(np.array([n]), rate)[0])); lit = math.exp(-since * 1.6)
        ev = p["every"]; nb = int(math.floor(gb * rate / ev + 1e-9)); since_b = gb * rate / ev - nb
        bass_k = semi(int(self.val(np.array([nb]), rate / ev)[0])) - 12 if p["keys_bass"] else None
        bass_k = None if bass_k is None or bass_k < lo else bass_k
        # case + felt strip
        cv.rect(0, y0 - 2.5, 172, 5, pal.ramp("bg", .25), .95 * a)
        cv.rect(0, y0 - 2.5, 172, 1.2, A(.55), .8 * a)
        for k in whites:
            x = xpos[k]; on = (k == lead_k)
            c = pal.ramp("pale", .7)                         # a step down from the staff's cream: staff stays the hero
            if on: c = c * (1 - lit) + E(.68) * lit
            cv.rect(x, y0 + hW / 2, kw - 1.2, hW, c, a)
            cv.rect(x - kw / 2 + 1.2, y0 + hW / 2, 1.0, hW, pal.ramp("body", .35), .55 * a)      # left shading
            cv.rect(x, y0 + hW - 1.5, kw - 1.2, 2.0, pal.ramp("body", .45), .7 * a)              # front lip
            if on and lit > .15: cv.glow(x, y0 + hW * .6, 9, E(.85), .55 * lit * a)
            if k == bass_k: cv.disc(x, y0 + hW - 5, 1.6, A(.8), a * (.55 + .45 * math.exp(-since_b * 1.2)))
        for k in range(lo, hi + 1):
            if (k % 12) in WHITE: continue
            x = xpos[k - 1] + kw / 2; on = (k == lead_k)
            c = pal.ramp("bg", .08)
            if on: c = c * (1 - lit) + E(.75) * lit
            cv.rect(x, y0 + hB / 2, kw * .6, hB, c, a)
            cv.rect(x - kw * .15, y0 + hB * .35, 1.0, hB * .55, pal.ramp("body", .5), .6 * a)      # sheen
            if on and lit > .15: cv.glow(x, y0 + hB * .5, 7, E(.85), .5 * lit * a)
            if k == bass_k: cv.disc(x, y0 + hB - 3, 1.4, A(.8), a)
        # soft reflection of the lit key on the floor below (dithered by the composite)
        if lead_k in xpos: cv.glow(xpos[lead_k], y0 + hW + 6, 10, E(.6), .25 * lit * a)

    def _fall_plan(self, lb):
        p = self.p; ev = p["every"]; rate_b = p["rate"] / ev; sp = p["spacing"] * ev
        gb_d = self.b0 + p["drop_to_bass_at"]
        half = cv_half = 100
        n_first = int(math.ceil(gb_d * rate_b + (-80 - p["playhead_x"]) / sp))
        def landed_at(n):
            k = max(0, n - n_first)
            return p["drop_to_bass_at"] + min(k, 7) * p["fall_stagger"] + p["fall_beats"]
        return n_first, landed_at

    def _draw_falls(self, cv, gb, lb, base):
        p, E = self.p, self.E; ev = p["every"]; rate_b = p["rate"] / ev
        n_first, landed_at = self._fall_plan(lb)
        for k in range(8):
            n = n_first + k; st = p["drop_to_bass_at"] + k * p["fall_stagger"]
            if not (st <= lb < st + p["fall_beats"]): continue
            u = ease((lb - st) / p["fall_beats"], "outCubic")
            d = int(self.val(np.array([n * ev]), p["rate"])[0])
            y_top, _ = self._head_y(d, p["y"] - 2 * p["gap"], p["gap"])
            y_bot, _ = self._head_y(int(self.val(np.array([n]), rate_b)[0]), base, p["gap"], bass=True)
            x = self.note_x(n * ev, gb, p["rate"], p["spacing"])
            y = y_top + (y_bot - y_top) * u
            for j in range(4): cv.disc(x, y - (j + 1) * 3 * (1 - u), .8, E(.8), .5 * (1 - j / 4) * (1 - u))
            cv.glow(x, y, 6, E(.9), .7); cv.ellipse(x, y, self.hx, self.hy, E(.95), 1.0, ang=-.35)

    def sfx(self, dur_b):
        p = self.p
        if p["mode"] == "every4" and p["drop_to_bass_at"] is not None:
            return [(p["drop_to_bass_at"] + k * p["fall_stagger"], "pop") for k in range(5)]
        return []

    def _parent_edge(self, cv, lb):
        """We start INSIDE a giant lit note head: its rim frames the screen, then grows past the edges and fades."""
        E = self.E; k = ease(min(1, lb / self.p["parent_beats"]), "inCubic")
        cx, cy = self.p["playhead_x"] + 20, self.p["y"] + 6
        rx, ry = (64 + 120 * k), (48 + 90 * k)
        wx, wy = cv.world_grid()
        a, c = math.cos(.35), math.sin(.35)
        u = ((wx - cx) * a - (wy - cy) * c) / rx; v = ((wx - cx) * c + (wy - cy) * a) / ry
        d = u * u + v * v
        out = (d > 1).astype(np.float32) * (1 - k) * .92
        cv._blend((slice(None), slice(None)), out, cv._col(E(.78)))
        rim = ((d > .86) & (d <= 1)).astype(np.float32) * (1 - k)
        cv._blend((slice(None), slice(None)), rim, cv._col(E(1.0)))
        sh = ((d > .55) & (d < .62) & (u < -.2) & (v < -.1)).astype(np.float32) * (1 - k) * .7   # specular arc
        cv._blend((slice(None), slice(None)), sh, cv._col(self.pal.ramp("pale", 1.0)))


def voss_mccartney(n, rows=12, seed=0):
    """Pink (1/f) noise by the Voss–McCartney algorithm: `rows` random sources, row k re-drawn every 2^k samples
    (on the trailing-zero count of the sample index), summed. Deterministic for a seed; returns zero-mean, unit-peak."""
    r = np.random.default_rng(seed)
    vals = r.uniform(-1, 1, rows); out = np.empty(n)
    for i in range(n):
        if i:
            k = (i & -i).bit_length() - 1
            if k < rows: vals[k] = r.uniform(-1, 1)
        out[i] = vals.sum() + r.uniform(-1, 1)
    out -= out.mean(); return out / (np.abs(out).max() or 1)


def white_noise(n, seed=0):
    r = np.random.default_rng(seed); x = r.uniform(-1, 1, n); return x / np.abs(x).max()


def brown_noise(n, seed=0, leak=.985):
    r = np.random.default_rng(seed); w = r.normal(0, 1, n); y = np.empty(n); acc = 0.0
    for i in range(n): acc = acc * leak + w[i]; y[i] = acc
    y -= np.convolve(y, np.ones(64) / 64, "same") * .0       # keep the slow drift
    y -= y.mean(); return y / (np.abs(y).max() or 1)


NOISES = {"white": white_noise, "pink": voss_mccartney, "brown": brown_noise}


class NoiseScope(Scene):
    """A lab CRT oscilloscope with stacked noise traces scrolling left: white (coral, jagged), pink 1/f (turquoise,
    Voss–McCartney) and brown (gök, slow drift). At `focus_at` the `focus_trace` thickens and glows, the others dim;
    `label_1975` puts a coral year plate on the bezel. Traces are pre-generated (seeded) and scroll by whole samples,
    so nothing jitters between frames."""
    defaults = {"traces": ["white", "pink", "brown"], "focus_trace": "pink", "focus_at": 3.0, "label_1975": True,
                "x": 0.0, "y": 14.0, "w": 150.0, "h": 116.0, "speed": 22.0, "amp": 12.0,
                "labels": {"white": "BEYAZ", "pink": "1/F", "brown": "KAHVE"}, "year": "1975"}
    COL = {"white": ("accent", .62), "pink": ("energy", .75), "brown": ("pale", .55)}

    def setup(self):
        n = 4096
        self.data = {k: NOISES[k](n, seed=int(self.rng.integers(1 << 30))) for k in self.p["traces"]}

    def focus(self, lb, dur_b):
        i = self.p["traces"].index(self.p["focus_trace"]) if self.p["focus_trace"] in self.p["traces"] else 0
        return (self.p["x"], self._lane_y(i))

    def _lane_y(self, i):
        p = self.p; n = len(p["traces"]); top = p["y"] - p["h"] / 2 + 10; inner = p["h"] - 20
        return top + inner * (i + .5) / n

    def draw(self, cv, lt, lb, dur_b):
        p, E, A, pal = self.p, self.E, self.A, self.pal
        x0, y0, w, h = p["x"], p["y"], p["w"], p["h"]
        # cabinet + bezel
        cv.glow(x0, y0, w * .55, E(.5), .22)
        cv.rect(x0 + 3, y0 + 4, w + 14, h + 18, pal.ramp("bg", 0), .7)                    # drop shadow
        cv.rect(x0, y0, w + 14, h + 18, pal.ramp("dim", .55), 1)
        cv.rect(x0, y0 - (h + 18) / 2 + 1.5, w + 12, 2, pal.ramp("pale", .55), 1)          # top bevel highlight
        cv.rect(x0, y0 + (h + 18) / 2 - 1, w + 14, 2, pal.ramp("bg", .3), 1)
        sx0, sx1 = x0 - w / 2, x0 + w / 2; sy0, sy1 = y0 - h / 2, y0 + h / 2
        cv.rect(x0, y0, w + 2, h + 2, pal.ramp("bg", .0), 1)
        cv.rect(x0, y0, w, h, pal.ramp("bg", .33), 1)
        cv.glow(x0, y0, w * .45, E(.35), .16)
        # graticule
        for gx in np.arange(sx0 + w / 8, sx1 - 1, w / 8):
            for gy in np.arange(sy0 + 2, sy1, 4): cv.points([gx], [gy], pal.ramp("dim", .9), .55)
        for gy in np.arange(sy0 + h / 6, sy1 - 1, h / 6):
            for gx in np.arange(sx0 + 2, sx1, 4): cv.points([gx], [gy], pal.ramp("dim", .9), .55)
        foc = max(0.0, min(1.0, (lb - p["focus_at"]) / .4)) if lb >= p["focus_at"] else 0.0
        foc = ease(foc, "outCubic")
        off = int(math.floor(lb * p["speed"]))
        xs = np.arange(sx0 + 22, sx1 - 4, 1.0); ns = len(xs)
        for i, k in enumerate(p["traces"]):
            yc = self._lane_y(i); d = self.data[k]
            seg = d[(off + np.arange(ns)) % len(d)]
            focus = k == p["focus_trace"]
            amp = p["amp"] * (1.0 + (.15 * foc if focus else 0))
            ys = yc - seg * amp
            ramp, tt = self.COL[k]; col = pal.ramp(ramp, tt + (.2 * foc if focus else 0))
            alpha = 1.0 if focus else 1 - .6 * foc
            # faint phosphor afterglow (previous sweep), then the trace
            cv.poly_outline(list(zip(xs, ys + 1.0)), pal.ramp(ramp, tt * .55), .35 * alpha, closed=False)
            cv.poly_outline(list(zip(xs, ys)), col, alpha, width=max(1, int(round(cv.cam.zoom * (1 + (1.2 * foc if focus else 0))))), closed=False)
            if focus and foc > 0:
                for j in range(0, ns, 6): cv.glow(xs[j], ys[j], 3.5, E(.85), .22 * foc)
            # beam head (right end) + lane label
            cv.glow(xs[-1], ys[-1], 4, col, .8 * alpha); cv.disc(xs[-1], ys[-1], 1.0, pal.ramp("pale", 1), alpha)
            lab = p["labels"].get(k, k.upper())
            draw_mini(cv, lab, sx0 + 11, yc - 1, 1.0, col, .95 * (1.0 if focus else 1 - .5 * foc))
            cv.line(sx0 + 20, yc, sx1 - 2, yc, .6, pal.ramp("dim", .8), .35)
        # scanlines + rolling CRT bar
        for yy in np.arange(sy0, sy1, 2): cv.line(sx0, yy, sx1, yy, .5, pal.ramp("bg", 0), .22)
        bar = sy0 + ((lt * 30) % (h + 20)) - 10
        if sy0 < bar < sy1: cv.rect(x0, bar, w, 5, pal.ramp("pale", .6), .06)
        # bezel furniture: knobs, power LED (beats), brand-less model plate, 1975 plate
        kb_y = sy1 + 5.5
        for j, kx in enumerate((sx0 + 10, sx0 + 24, sx0 + 38)):
            cv.disc(kx, kb_y, 3.2, pal.ramp("pale", .4)); cv.disc(kx, kb_y, 2.2, pal.ramp("pale", .7))
            a = lt * (.6 + .3 * j) + j
            cv.line(kx, kb_y, kx + 2 * math.cos(a), kb_y + 2 * math.sin(a), .7, pal.ramp("bg", .2))
        led = pulse(lb, 1.0, 6.0)
        cv.disc(sx1 - 6, kb_y, 1.4, A(.35 + .5 * led)); cv.glow(sx1 - 6, kb_y, 4, A(.6), .5 * led)
        draw_mini(cv, "OSİLOSKOP", x0 + 8, sy0 - 5, 1.0, pal.ramp("pale", .85), .8)
        if p["label_1975"] and lb >= p["focus_at"]:
            k = ease(min(1, (lb - p["focus_at"]) / .3), "outCubic"); sc = 1 + .6 * (1 - k)
            cv.rect(sx1 - 22, kb_y, 22 * sc, 9 * sc, A(.45), k)
            draw_mini(cv, p["year"], sx1 - 22, kb_y, 1.0 * sc, pal.ramp("pale", 1.0), k)
            cv.glow(sx1 - 22, kb_y, 8, A(.6), .4 * (1 - k) + .15)


class SeriesTree(Scene):
    """The recursion of an integer series as a binary tree growing one level per `grow_every` beats: a seed node a(0)
    on top, node n has children 2n (left, coral edge) and 2n+1 (right, turquoise edge) — for Nørgård: −a(n) and a(n)+1.
    Nodes are note heads with their signed value in micro digits; the leaf row also bends into the melody's contour.
    leaves_play: on every 16th the path root → ancestor of the note sounding now (index floor(beat·rate)) lights up;
    on beats (index ≡ 0 mod 4) that ancestor has the SAME value as the sounding note (a(4n) = a(n))."""
    defaults = {"series": "norgard", "levels": 5, "grow_every": 1.0, "leaves_play": True, "show_rule": True,
                "rate": 4, "x": 0.0, "y_top": -50.0, "row": 23.0, "width": 172.0, "edge_beats": .5}

    def on_bind(self):
        self.period = int(round(self.total * self.p["rate"])) if self.loop and self.total else None

    def _pos(self, n):
        L = n.bit_length() - 1 if n > 0 else -1
        p = self.p
        if n == 0: return p["x"], p["y_top"]
        k = n - (1 << L); cnt = 1 << L
        x = p["x"] - p["width"] / 2 + (k + .5) * p["width"] / cnt
        y = p["y_top"] + p["row"] * (L + 1)
        if L == p["levels"]: y -= series_value(p["series"], n) * 1.6          # leaf row = the melody contour
        return x, y

    def _appear(self, n):
        L = n.bit_length() - 1 if n > 0 else -1
        if n == 0: return 0.0
        k = n - (1 << L); cnt = 1 << L
        return (L) * self.p["grow_every"] + .5 * self.p["grow_every"] * k / cnt

    def focus(self, lb, dur_b): return self._pos(1)

    def draw(self, cv, lt, lb, dur_b):
        p, E, A, pal = self.p, self.E, self.A, self.pal
        top = (1 << (p["levels"] + 1)) - 1
        gb = self.gbeat(lb)
        # current note + its ancestor path in the visible tree
        m = int(series_index(gb, p["rate"], self.period)); path = set()
        anc = None
        if p["leaves_play"] and m > 0:
            grown = max(0, min(p["levels"], int(math.floor(lb / p["grow_every"]))))
            a_ = m
            while a_ > (1 << (grown + 1)) - 1: a_ >>= 1
            if self._appear(a_) <= lb: anc = a_
            q = anc or 0
            while q > 0: path.add(q); q >>= 1
        on_beat = (m % 4 == 0); since = gb * p["rate"] - math.floor(gb * p["rate"])
        cv.glow(p["x"], p["y_top"] + p["row"] * 3, 120, E(.4), .12)
        # edges
        for n in range(1, top + 1):
            par = n >> 1 if n > 1 else 0
            t0 = self._appear(n)
            if lb < t0: continue
            k = ease(min(1, (lb - t0) / p["edge_beats"]), "outCubic")
            (xa, ya), (xb, yb) = self._pos(par), self._pos(n)
            left = (n % 2 == 0)
            col = A(.5) if left else E(.55)
            if n == 1: col = pal.ramp("pale", .6)
            hot = n in path
            cv.line(xa, ya, xa + (xb - xa) * k, ya + (yb - ya) * k, 1.6 if hot else .9, E(1.0) if hot else col, 1.0 if hot else .75)
            if hot: cv.glow((xa + xb) / 2, (ya + yb) / 2, 5, E(.9), .45)
        # nodes
        for n in range(0, top + 1):
            t0 = self._appear(n) + (.25 if n else 0)
            if lb < t0 - .25 and n: continue
            k = ease(min(1, max(0, (lb - (t0 - .25)) / .3)), "outCubic") if n else 1.0
            pop = 1 + .6 * math.sin(min(1, max(0, (lb - (t0 - .25)) / .3)) * math.pi) if n else 1.0
            x, y = self._pos(n); L = n.bit_length() - 1 if n else -1
            v = int(series_value(p["series"], n))
            size = {-1: 1.25, 0: 1.25, 1: 1.15, 2: 1.0, 3: .85, 4: .62, 5: .48}.get(L, .45) * pop
            base_c = A(.62) if v < 0 else (E(.75) if v > 0 else pal.ramp("pale", .95))
            hot = (n == anc); c = E(1.0) if hot else base_c
            if hot:
                cv.glow(x, y, 7 + 4 * (on_beat and since < .5), E(.9), .9)
            cv.ellipse(x, y, 2.9 * size, 2.15 * size, pal.ramp("bg", .1), k, ang=-.35)
            cv.ellipse(x, y, 2.6 * size, 1.9 * size, c, k, ang=-.35)
            if L <= 4:
                txt = ("+" if v > 0 else "") + str(v) if v else "0"
                draw_mini(cv, txt, x, y - 6.5 * max(size, .7) - (1 if L <= 1 else 0), 1.0 if L >= 2 else 1.0,
                          pal.ramp("pale", 1.0) if not hot else E(1.0), k)
        # the note that sounds right now drops out of the leaf below (the tree continues beyond the frame)
        if anc is not None and anc >= (1 << p["levels"]):
            x, y = self._pos(anc)
            for j in range(4):
                yy = y + 6 + j * 4 + since * 4
                cv.disc(x, yy, .8, E(.9), .8 * (1 - j / 4))
            if on_beat and since < .6:
                cv.ring(x, y, 4 + 8 * since, .8, E(1.0), 1 - since / .6)
                draw_mini(cv, "=" , x + 6, y + 9, 1.0, E(1.0), 1 - since / .6)

    def sfx(self, dur_b):
        return []


class ShepardStairs(Scene):
    """An endless (Shepard) spiral staircase of piano keys: one chromatic octave (`per_turn` keys) per turn of a helix.
    A glowing ♪ sprite hops up one key every 1/climb_rate beats while the helix turns one key back and sinks one step,
    so the sprite always stands front-centre and never gets higher. Key brightness is a Gaussian over height (the
    visual twin of the Shepard tone's loudness curve), so the top and bottom dissolve into the night.
    ring_countdown_from: a coral ring contracts around the sprite while turquoise glow builds; freeze_at: the climb
    stops (held breath) while dust/layers keep moving."""
    defaults = {"per_turn": 12, "climb_rate": 2, "rot_per_beat": 0.0, "ring_countdown_from": 4, "freeze_at": 7.5,
                "x": -14.0, "y": 30.0, "r_in": 9.0, "r_out": 58.0, "dh": 8.0, "th": 5.0, "pitch": .55, "front_angle": .45,
                "sigma": 9.0, "span": 20, "hop_frac": .4, "hop_h": 10.0}
    BLACK = {1, 3, 6, 8, 10}

    def _state(self, lb):
        p = self.p; lbf = min(lb, p["freeze_at"])
        h = max(0.0, lbf) * p["climb_rate"]; k = math.floor(h); f = h - k
        e = ease(min(1, f / p["hop_frac"]), "inOutSine")
        return lbf, k + e, f

    def _proj(self, r, th, Z):
        """helix-local polar (r, angle; 0 = facing camera) + height → screen x, y, depth (bigger = nearer)."""
        p = self.p
        return p["x"] + r * math.sin(th), p["y"] + r * math.cos(th) * p["pitch"] - Z, r * math.cos(th) + Z * .35

    def _sprite_pos(self, lbf, sc, f):
        p = self.p
        hop = math.sin(math.pi * min(1, f / p["hop_frac"])) * p["hop_h"] if f < p["hop_frac"] else 0.0
        r = (p["r_in"] + p["r_out"]) * .55
        x, y, _ = self._proj(r, p["front_angle"], 0.0)
        return x, y - hop - 8, 0

    def focus(self, lb, dur_b):
        lbf, sc, f = self._state(lb)
        x, y, _ = self._sprite_pos(lbf, sc, f); return x, y

    def _key(self, cv, j, rel, spin, fade, glow_key):
        p, pal = self.p, self.pal; N = p["per_turn"]; dth = TAU / N
        black = j % 12 in self.BLACK
        th0 = rel * dth + spin
        Z = rel * p["dh"] + (2.0 if black else 0.0)
        r0 = p["r_in"]; r1 = p["r_out"] * (.78 if black else 1.0)
        half = dth * (.40 if black else .47)
        n = 5
        outer = [self._proj(r1, th0 - half + 2 * half * i / n, Z) for i in range(n + 1)]
        inner = [self._proj(r0, th0 + half - 2 * half * i / n, Z) for i in range(n + 1)]
        top = [(q[0], q[1]) for q in outer + inner]
        front = math.cos(th0) > 0
        # riser face: outer rim when the key faces us, inner rim on the far side
        rim = outer if front else inner
        face = [(q[0], q[1]) for q in rim] + [(q[0], q[1] + p["th"]) for q in reversed(rim)]
        side = pal.ramp("bg", .55) if black else pal.ramp("body", .34 + .12 * max(0, math.cos(th0)))
        cv.poly(face, fade(side), 1.0)
        if black:
            cv.poly(top, fade(pal.ramp("bg", .18)), 1.0); cv.poly_outline(top, fade(pal.ramp("body", .6)), 1.0)
        else:
            cv.poly(top, fade(pal.ramp("pale", 1.0)), 1.0); cv.poly_outline(top, fade(pal.ramp("body", .58)), 1.0)
        if glow_key:
            cx_ = sum(t[0] for t in top) / len(top); cy_ = sum(t[1] for t in top) / len(top)
            cv.glow(cx_, cy_, 12, self.E(.85), .5)

    def draw(self, cv, lt, lb, dur_b):
        p, E, A, pal = self.p, self.E, self.A, self.pal
        N = p["per_turn"]; lbf, sc, f = self._state(lb); dth = TAU / N
        spin = math.radians(p["rot_per_beat"] * lbf) + p["front_angle"]
        cv.glow(p["x"], p["y"], 95, pal.ramp("body", .5), .22)
        cv.glow(p["x"], p["y"] - 10, 45, E(.5), .14)
        k0 = math.floor(sc)
        keys = []
        for j in range(k0 - p["span"], k0 + p["span"] + 1):
            rel = j - sc
            bri = math.exp(-.5 * (rel / p["sigma"]) ** 2)
            if bri < .04: continue
            th0 = rel * dth + spin
            keys.append((math.cos(th0) * p["r_out"] * .5 + rel * p["dh"] * .35, j, rel, bri))
        keys.sort(key=lambda t: t[0])
        bg = pal.ramp("bg", .08)
        # central column: drawn after the far half, before the near half
        pole_done = False
        for depth, j, rel, bri in keys:
            if not pole_done and depth > 0:
                self._pole(cv, lt, sc); pole_done = True
            k = 1 - bri
            fade = lambda c, k=k: c * (1 - k) + bg * k
            self._key(cv, j, rel, spin, fade, abs(rel) < .5 and f >= p["hop_frac"] * .8)
        if not pole_done: self._pole(cv, lt, sc)
        # handrail: dotted helix just outside the keys, coral
        for i in range(-90, 91):
            rel = i / 6.0
            th = rel * dth + spin
            if math.cos(th) < 0: continue
            x, y, _ = self._proj(p["r_out"] + 4, th, rel * p["dh"] + 9)
            bri = math.exp(-.5 * (rel / p["sigma"]) ** 2)
            if i % 2 == 0: cv.points([x], [y], A(.6), alpha=.75 * bri)
        # sprite (♪) with hop, motion sparks
        x, y, _ = self._sprite_pos(lbf, sc, f)
        land = p["hop_frac"] <= f < p["hop_frac"] + .15
        cv.glow(x, y, 9, E(.8), .55)
        sz = 3.0 if not land else 2.6
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            draw_bitmap(cv, Bitmap(EIGHTH, x + ox, y + oy, sz), pal.ramp("bg", .02))
        draw_bitmap(cv, Bitmap(EIGHTH, x, y, sz), E(1.0))
        for k in range(5):
            u = ((lt * .7 + k / 5) % 1.0)
            cv.points([x + 9 * math.sin(k * 2.3 + lt)], [y - 6 - u * 26], E(.85), alpha=1 - u)
        # countdown ring + rising turquoise glow
        if lb >= p["ring_countdown_from"]:
            k = min(1.0, (lbf - p["ring_countdown_from"]) / max(.1, p["freeze_at"] - p["ring_countdown_from"]))
            r = 46 - 34 * ease(k, "inCubic")
            cv.ring(x, y, r, 1.6, A(.5 + .3 * k), .95, dashes=10, phase=lt * .5)
            cv.ring(x, y, r + 3, .7, A(.4), .5)
            cv.glow(x, y, 12 + 20 * k, E(.8), .25 + .7 * k ** 2)

    def _pole(self, cv, lt, sc):
        p, pal = self.p, self.pal
        x = p["x"]; w = p["r_in"] * .8
        for yy in range(-160, 161, 2):
            Z = -yy + p["y"]
            rel = Z / p["dh"]
            bri = math.exp(-.5 * (rel / (p["sigma"] * 1.1)) ** 2)
            if bri < .05: continue
            cv.line(x - w, yy, x + w, yy, 2.0, pal.ramp("body", .22 + .1 * bri), .9 * bri)
        # light pulses rising up the column (the "always rising" tell)
        for k in range(3):
            u = (lt * .5 + k / 3) % 1.0
            yy = p["y"] + 60 - u * 160
            cv.glow(x, yy, 5, self.E(.7), .5 * math.sin(math.pi * u))


from .scenes import SCENES  # noqa: E402
SCENES.update({"fractal_staff": FractalStaff, "noise_scope": NoiseScope, "series_tree": SeriesTree, "shepard_stairs": ShepardStairs})
