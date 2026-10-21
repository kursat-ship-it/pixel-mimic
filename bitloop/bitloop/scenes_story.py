"""Story scenes (reusable, topic-agnostic): a hooded pixel hero with a hovering book of the future at a forked road
over a prophecy piano-roll, Laplace's many-eyed demon over a deterministic billiard table, a domino run before a
pendulum clock (optionally split: mechanical top / a domino that chooses, bottom), a Libet clock with an EEG strip
(readiness ramp → noisy trials whose average is the ramp), and a dice → branching futures tree.
All draw in world units (≈ art px at zoom 1, origin = frame centre, y down) as pure functions of time; every scene is
already populated at lb = 0 (pre-rolled) and keeps content in the lower third."""
import math
import numpy as np
from .scenes import Scene, ease, pulse, TAU
from .theory import series_value, series_index
from .bitmap import Bitmap, draw_bitmap
from .sprites import HERO, draw_sprite, hero_frame, _hex


def _arr(rows):
    return np.array([[c == "#" for c in r] for r in rows])


ARROW_L = _arr([
    ".....##.......", "....###.......", "...####.......", "..############", ".#############", "##############",
    "##############", ".#############", "..############", "...####.......", "....###.......", ".....##.......",
])
MINI_HERO = [   # 7×7 portrait for the book page
    "..ooo..", ".occco.", "occcco.", "ocfffco", "ocefeco", ".offfo.", "..sss..",
]
CROSS = _arr(["#...#", ".#.#.", "..#..", ".#.#.", "#...#"])


def _wrap_b(gb, total):
    return gb % total if total else gb


class FutureBook(Scene):
    """The hero scene: a hooded pixel hero at a forked road (two glowing doorways), a hovering BOOK OF THE FUTURE whose
    right page shows one big arrow (+ a tiny portrait of the hero), pages flipping every `page_flip_every` beats with a
    3-frame flip, a sky clock that ticks on beats with a 2-beat pendulum, and a PROPHECY ROLL in the lower third: a
    one-row piano roll of `roll_series` on the global 8th grid (ghost = future, türkuaz = sounding now, a small halo on
    the next ghost = the whisper voice one 8th early).
    mode read: hero reads, steps toward the arrow at `step_at`, looks back at the book. focus → arrow after lb 5.
    mode avoid (twist): hero reads, at `turn_at` pivots and walks to the OTHER door; the arrow cracks (`ink_crack_at`);
      on the roll, predicted ghosts of `roll_series` that `actual_series` (phase = section) does not play become ✗.
    mode open: the closed cover (as on the desk) opens over `open_beats` and settles exactly into the read-mode frame at
      the loop seam (everything is a function of the global beat modulo the film length)."""
    defaults = {"mode": "read", "arrow": "left", "page_flip_every": 0.5, "fork": True, "roll": True,
                "roll_series": "kehanet", "actual_series": None, "step_at": 3.0, "turn_at": 3.0, "ink_crack_at": 3.0,
                "sprite_scale": 2.4, "open_from_cover": True, "open_beats": 2.0, "converge_to_frame0": False,
                "roll_rate": 2, "roll_y": 122.0, "roll_lanes": [-1, 7], "playhead_x": -38.0, "slot_w": 12.0,
                "hero_x": 0.0, "hero_y": 78.0, "book_x": 0.0, "book_y": 70.0, "page_w": 26.0, "page_h": 30.0, "step_dx": -34.0, "clock": True, "whisper": 1}

    def on_bind(self):
        self.n0_actual = int(math.ceil(self.b0 * self.p["roll_rate"] - 1e-9))

    # --------------------------------------------------------------- state
    def _gb(self, lb):
        return _wrap_b(self.gbeat(lb), self.total)

    def _hero(self, lb):
        """→ (x, y, frame, flip, scale_k)"""
        p = self.p; m = p["mode"]; x, y = p["hero_x"], p["hero_y"]
        idle = hero_frame("idle", self._gb(lb), 0.0)
        reading = HERO["read"] if idle is HERO["front"] else HERO["blink"]
        if m == "read":
            s0 = p["step_at"]
            if lb < s0: return x, y, reading, False, 1.0
            dx = p["step_dx"]
            if lb < s0 + 1:
                k = ease(lb - s0, "inOutSine")
                return x + dx * k, y - 8 * k, hero_frame("walk", lb), dx < 0, 1 - .05 * k
            fr = HERO["look_r"] if lb < s0 + 3 else (HERO["front"] if idle is HERO["front"] else HERO["blink"])
            if s0 + 1 <= lb < s0 + 1.2: fr = HERO["wow"]
            return x + dx, y - 8, fr, False, .95
        if m == "avoid":
            t0 = p["turn_at"]
            if lb < t0 - 1: return x, y, reading, False, 1.0
            if lb < t0: return x, y, (HERO["look_l"] if lb < t0 - .5 else HERO["wow"]), False, 1.0
            if lb < t0 + .25: return x, y, HERO["turn"], False, 1.0
            k = ease(min(1.0, (lb - t0 - .25) / 3.0), "inOutSine")
            return x + 40 * k, y - 22 * k, hero_frame("walk", lb), False, 1 - .22 * k
        return x, y, reading, False, 1.0          # open

    def _book_open(self, lb):
        if self.p["mode"] != "open" or not self.p["open_from_cover"]: return 1.0
        return ease(min(1.0, max(0.0, lb) / self.p["open_beats"]), "inOutCubic")

    def _book_pos(self, lb):
        gb = self._gb(lb)
        return self.p["book_x"], self.p["book_y"] + 1.5 * math.sin(gb * math.pi / 2)        # 4-beat hover bob

    def focus(self, lb, dur_b):
        bx, by = self._book_pos(lb)
        if self.p["mode"] == "avoid" and lb < 1.0:
            x, y, *_ = self._hero(lb); return x, y - 32
        return bx + 12, by - 1

    # --------------------------------------------------------------- draw
    def draw(self, cv, lt, lb, dur_b):
        p, pal, E, A = self.p, self.pal, self.E, self.A
        gb = self._gb(lb)
        self._ground(cv, gb)
        if p["clock"]: self._clock(cv, gb)
        if p["fork"]: self._fork(cv, gb, lb)
        hx, hy, fr, flip, sk = self._hero(lb)
        behind = abs(hx - p["hero_x"]) < 12        # behind the hovering book only while standing at the junction
        if not behind: self._book(cv, gb, lb)
        cv.glow(hx, hy - 20, 22, pal.ramp("body", .6), .18)
        draw_sprite(cv, fr, hx, hy + .5 * pulse(gb, 1.0, 6.0) * 0, p["sprite_scale"] * sk, flip)
        if behind: self._book(cv, gb, lb)
        if p["roll"]: self._roll(cv, gb, lb)

    def _ground(self, cv, gb):
        pal = self.pal
        hz = 30.0
        cv.mask_fill(lambda x, y: y > hz, pal.ramp("bg", .55), 1.0)
        cv.mask_fill(lambda x, y: (y > hz) & (y < hz + 2), pal.ramp("body", .22), 1.0)
        # dithered ground rows (perspective bands)
        for i in range(7):
            yy = hz + 4 + (i ** 1.6) * 4.2
            cv.line(-120, yy, 120, yy, .7, pal.ramp("bg", .9), .55)

    def _clock(self, cv, gb):
        pal, E, A = self.pal, self.E, self.A
        cx, cy, R = 0.0, -30.0, 22.0
        # pendulum first (behind the face): 2-beat period
        ang = math.radians(22) * math.sin(gb * math.pi)
        bx, by = cx + 40 * math.sin(ang), cy + 40 * math.cos(ang)
        cv.line(cx, cy, bx, by, 1.0, pal.ramp("body", .38), .9)
        cv.disc(bx, by, 4.2, pal.ramp("body", .45), 1.0); cv.disc(bx - 1, by - 1, 2.0, pal.ramp("body", .7), 1.0)
        cv.glow(bx, by, 8, E(.6), .12 + .2 * pulse(gb, 1.0, 5))
        cv.disc(cx, cy, R + 2, pal.ramp("bg", .7), 1.0)
        cv.disc(cx, cy, R, pal.ramp("body", .2), 1.0)
        cv.ring(cx, cy, R, 1.4, pal.ramp("body", .5), 1.0)
        for k in range(12):
            a = k / 12 * TAU
            r0 = R - (4 if k % 3 == 0 else 2.5)
            cv.line(cx + r0 * math.sin(a), cy - r0 * math.cos(a), cx + (R - 1) * math.sin(a), cy - (R - 1) * math.cos(a),
                    1.0 if k % 3 else 1.4, pal.ramp("pale", .8 if k % 3 == 0 else .55), 1.0)
        sa = math.floor(gb) / 16 * TAU                                  # second hand: one step per beat
        ma = gb / 80 * TAU                                               # minute hand: once per film loop
        cv.line(cx, cy, cx + 12 * math.sin(ma), cy - 12 * math.cos(ma), 1.6, pal.ramp("pale", .8), 1.0)
        cv.line(cx, cy, cx + 17 * math.sin(sa), cy - 17 * math.cos(sa), 1.0, A(.65), 1.0)
        cv.disc(cx, cy, 1.6, A(.7), 1.0)

    def _fork(self, cv, gb, lb):
        """Forked road in perspective: trunk from the camera to the hero, two branches curving away to doorways."""
        pal, E, A = self.pal, self.E, self.A
        jx, jy = self.p["hero_x"], self.p["hero_y"] - 2
        dirt, dirt_d = pal.ramp("body", .24), pal.ramp("body", .16)

        def band(path, w0, w1, col):
            L, R = [], []
            for i, (x, y) in enumerate(path):
                u = i / (len(path) - 1); w = w0 + (w1 - w0) * u
                x2, y2 = path[min(i + 1, len(path) - 1)]; x1, y1 = path[max(i - 1, 0)]
                tx, ty = x2 - x1, y2 - y1; n = math.hypot(tx, ty) or 1
                L.append((x - ty / n * w, y + tx / n * w)); R.append((x + ty / n * w, y - tx / n * w))
            cv.poly(L + R[::-1], col, 1.0)

        def curve(p0, p1, p2, k=12):
            return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                     (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in np.linspace(0, 1, k)]
        self._branch = {}
        for side in (-1, 1):
            path = curve((jx, jy + 2), (side * 58, jy + 2), (side * 66, 32))
            band(path, 6, 2.2, dirt_d); band(path, 4.5, 1.5, dirt)
            for t in (.15, .35, .55, .75, .92):                            # cobbles: read as ground, not as arms
                x, y = path[int(t * (len(path) - 1))]
                cv.ellipse(x, y, 2.6 - 1.6 * t, 1.0 - .5 * t, pal.ramp("body", .36), .9)
            self._branch[side] = path
        band([(0, 175), (0, jy)], 46, 10, dirt_d); band([(0, 175), (0, jy)], 40, 8, dirt)
        # stepping stones down the trunk (perspective), drifting toward camera (period 1 beat → loop-safe)
        for i in range(6):
            u = ((i + (gb % 1.0)) / 6.0)
            yy = jy + 8 + (175 - jy - 8) * u ** 1.7
            w = 3 + 11 * u ** 1.4
            cv.ellipse(0, yy, w, w * .32, pal.ramp("body", .34), .9)
        # doorways at the ends: türkuaz (the written path) and mercan (the other one)
        for side, ramp in ((-1, "energy"), (1, "accent")):
            dx, dy = side * 66, 31
            col = pal.ramp(ramp, .55); hot = pal.ramp(ramp, .9)
            cv.glow(dx, dy - 12, 20, col, .4 + .12 * math.sin(gb * math.pi))
            frame, stone = pal.ramp("body", .55), pal.ramp("body", .3)
            cv.rect(dx, dy - 11, 19, 23, frame, 1.0); cv.ellipse(dx, dy - 22, 9.5, 6.5, frame, 1.0)      # stone arch
            cv.rect(dx, dy - 11, 16, 22, stone, 1.0); cv.ellipse(dx, dy - 22, 8, 5, stone, 1.0)
            cv.rect(dx, dy - 10, 11, 20, col, 1.0); cv.ellipse(dx, dy - 20, 5.5, 4, col, 1.0)               # light
            cv.rect(dx, dy - 4, 11, 8, hot, .75)
            cv.line(dx - 9.5, dy - 3, dx - 9.5, dy - 18, 1, pal.ramp("body", .7), 1.0)                    # lit jamb
            cv.rect(dx, dy + 1, 23, 2, frame, 1.0); cv.rect(dx, dy + 3, 27, 1.6, stone, 1.0)                # steps
        # lamps along both branches blink on 8ths (period 4 slots → loop-safe at 160 slots)
        n = int(math.floor(gb * 2 + 1e-9))
        for side, ramp in ((-1, "energy"), (1, "accent")):
            path = self._branch[side]
            for i, t in enumerate((.3, .55, .8)):
                x, y = path[int(t * (len(path) - 1))]
                x += side * (7 - 4 * t)
                h = 7 - 3 * t
                lit = ((n + i) % 4) == (0 if side < 0 else 2)
                cv.line(x, y, x, y - h, .9, pal.ramp("body", .5), 1.0)
                c = pal.ramp(ramp, .95 if lit else .45)
                cv.disc(x, y - h, 1.3, c, 1.0)
                if lit: cv.glow(x, y - h, 6, pal.ramp(ramp, .7), .6)

    def _book(self, cv, gb, lb):
        p, pal, E, A = self.p, self.pal, self.E, self.A
        bx, by = self._book_pos(lb)
        op = self._book_open(lb)
        PW, PH = p["page_w"], p["page_h"]
        cv.glow(bx, by, 34, E(.55), .28 + .12 * pulse(gb, 1.0, 4))
        leather, leather_d, rim = pal.ramp("body", .4), pal.ramp("body", .25), pal.ramp("body", .62)
        if op < 1.0:
            # closed → open: the cover swings open around the spine (left edge), seen from the front
            k = op
            cover_w = PW * math.cos(k * math.pi)                          # + : cover over the right page, − : open left
            # back cover + right page
            cv.rect(bx + PW / 2 + 1, by, PW + 3, PH + 3, leather_d, 1.0)
            if k > .02: self._page(cv, bx + PW / 2 + .5, by, PW, PH, gb, lb, right=True, alpha=min(1, k * 2))
            x0 = bx + 1
            quad = [(x0, by - PH / 2 - 1.5), (x0 + cover_w, by - PH / 2 - 1.5 - 3 * math.sin(k * math.pi)),
                    (x0 + cover_w, by + PH / 2 + 1.5 + 3 * math.sin(k * math.pi)), (x0, by + PH / 2 + 1.5)]
            if abs(cover_w) > .6:
                cv.poly(quad, leather if cover_w > 0 else leather_d, 1.0)
                cv.poly_outline(quad, rim, 1.0)
                if cover_w > 6:   # emboss (eye + frame) on the closed cover
                    cx_ = x0 + cover_w / 2
                    cv.rect(cx_, by, cover_w - 5, PH - 4, pal.ramp("pale", .55), .6)
                    cv.rect(cx_, by, cover_w - 7, PH - 6, leather, 1.0)
                    from .bitmap import draw_mark
                    draw_mark(cv, pal, cx_, by - 4, .8 * cover_w / PW, glow=0, outline=pal.ramp("bg", .05))
            if k > .5:
                self._page(cv, bx - PW / 2 - .5, by, PW, PH, gb, lb, right=False, alpha=(k - .5) * 2)
            cv.line(bx, by - PH / 2 - 1, bx, by + PH / 2 + 1, 1.4, pal.ramp("bg", .2), 1.0)
            return
        # open book: covers, page stack edges, two pages, flipping page
        cv.rect(bx, by + 1.5, 2 * PW + 5, PH + 4, leather_d, 1.0)
        cv.rect(bx, by + 1, 2 * PW + 3, PH + 2, pal.ramp("pale", .55), 1.0)          # page-stack edge
        self._page(cv, bx - PW / 2 - .5, by, PW, PH, gb, lb, right=False)
        self._page(cv, bx + PW / 2 + .5, by, PW, PH, gb, lb, right=True)
        cv.line(bx, by - PH / 2, bx, by + PH / 2, 1.2, pal.ramp("pale", .5), 1.0)
        # 3-frame page flip at the start of every page_flip_every window (0.2 beat ≈ 3 frames at 120 BPM)
        fe = p["page_flip_every"]; ph = (gb % fe) / fe
        fdur = .2 / fe
        if ph < fdur:
            f = int(ph / fdur * 3)                                        # 0, 1, 2
            w = (PW * .3, 2.5, -PW * .55)[f]; lift = (3, 6, 3)[f]           # stays clear of the arrow
            quad = [(bx, by - PH / 2), (bx + w, by - PH / 2 - lift), (bx + w, by + PH / 2 + lift * .4), (bx, by + PH / 2)]
            cv.poly(quad, pal.ramp("pale", .9 if f != 1 else .75), 1.0)
            cv.poly_outline(quad, pal.ramp("pale", .55), 1.0)

    def _page(self, cv, x, y, w, h, gb, lb, right, alpha=1.0):
        p, pal, E, A = self.p, self.pal, self.E, self.A
        cv.rect(x, y, w, h, pal.ramp("pale", 1.0), alpha)
        # spine-side dither shadow
        sx = x - w / 2 + 1 if right else x + w / 2 - 1
        cv.rect(sx, y, 2, h, _hex("#B8CDF2"), alpha)
        cv.matte(x, y, w, h, .85)
        if not right:
            # handwriting lines (no real text): rows of short strokes, Sis/Gök
            rng = np.random.default_rng(int(math.floor(gb / p["page_flip_every"])) % 8 + 7)
            for r in range(7):
                yy = y - h / 2 + 4 + r * 3.1
                xx = x - w / 2 + 3
                while xx < x + w / 2 - 4:
                    L = float(rng.uniform(2, 6))
                    cv.line(xx, yy, min(xx + L, x + w / 2 - 4), yy, .9, pal.ramp("pale", .45), .9 * alpha)
                    xx += L + 1.6
            return
        # the arrow (≥ 12 dots tall), deep-firuze outline for contrast on cream, türkuaz light fill
        ax, ay = x + 3, y - 4
        arr = ARROW_L if self.p["arrow"] == "left" else ARROW_L[:, ::-1]
        crack = self._crack(lb)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            draw_bitmap(cv, Bitmap(arr, ax + dx, ay + dy, 1.0), _hex("#0B4F5C"), alpha)
        fill = E(.72) if crack < 1 else E(.6) * .5 + A(.6) * .5
        draw_bitmap(cv, Bitmap(arr, ax, ay, 1.0), fill, alpha)
        cv.glow(ax, ay, 9, E(.7), (.25 + .2 * pulse(gb, .5, 5)) * alpha)
        if crack > 0: self._draw_crack(cv, ax, ay, crack, alpha)
        # tiny portrait of the hero under the arrow
        L = {}
        for r, row in enumerate(MINI_HERO):
            for c, ch in enumerate(row):
                if ch != ".": L.setdefault(ch, np.zeros((7, 7), bool))[r, c] = True
        from .sprites import ROLES
        for ch, m in L.items():
            draw_bitmap(cv, Bitmap(m, x + 3, y + 9, 1.0), _hex(ROLES[ch]), alpha)

    def _crack(self, lb):
        p = self.p
        if p["mode"] != "avoid": return 0.0
        k = (lb - p["ink_crack_at"]) / .2                                   # 3 frames
        return 0.0 if k < 0 else min(3.0, math.floor(k) + 1)

    def _draw_crack(self, cv, ax, ay, stage, alpha):
        A = self.A
        segs = [[(-1, -6), (1, -2), (-1, 1), (2, 4), (0, 7)], [(1, -2), (5, -1), (8, -3)], [(-1, 1), (-5, 2), (-7, 0)]]
        for i, s in enumerate(segs[:int(stage)]):
            pts = [(ax + a, ay + b) for a, b in s]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                cv.line(x0, y0, x1, y1, 1.1, A(.55), alpha)
        cv.glow(ax, ay, 7, A(.6), .4 * alpha)

    def _roll(self, cv, gb, lb):
        p, pal, E, A = self.p, self.pal, self.E, self.A
        rate, sw, px0 = p["roll_rate"], p["slot_w"], p["playhead_x"]
        lo, hi = p["roll_lanes"]; nl = hi - lo + 1
        y0 = p["roll_y"]; lh = 3.4; top = y0 - nl * lh / 2
        cv.rect(0, y0, 178, nl * lh + 8, pal.ramp("bg", .02), .92)
        cv.rect(0, y0 - nl * lh / 2 - 4, 178, 1, pal.ramp("body", .35), 1.0)
        cv.rect(0, y0 + nl * lh / 2 + 4, 178, 1, pal.ramp("body", .35), 1.0)
        for i in range(nl):
            if (lo + i) % 7 == 0:
                cv.rect(0, top + (hi - (lo + i)) * lh + lh / 2, 178, .8, pal.ramp("bg", .9), 1.0)
        now = gb * rate; n_now = int(math.floor(now + 1e-9))
        name = p["roll_series"]; act = p["actual_series"]
        for n in range(n_now - 5, n_now + 10):
            x = px0 + (n - now) * sw
            if x < -95 or x > 95: continue
            nn = n % int(self.total * rate) if self.total else n
            v = int(series_value(name, nn))
            yy = top + (hi - v) * lh + lh / 2
            played, wrong = v, False
            if act and self.p["mode"] == "avoid" and n >= self.n0_actual and n <= n_now:
                played = int(series_value(act, n - self.n0_actual)); wrong = played != v     # what was really played
            yp = top + (hi - played) * lh + lh / 2
            past, cur = n < n_now, n == n_now
            fade = max(0.0, 1 - abs(x) / 96) ** .5
            if n > n_now:   # future: ghost outline (whisper halo on the next one)
                cv.poly_outline([(x + .5, yy - 1.5), (x + sw - 1.5, yy - 1.5), (x + sw - 1.5, yy + 1.5), (x + .5, yy + 1.5)],
                                pal.ramp("body", .62), fade)
                if n - n_now == p["whisper"]: cv.glow(x + sw / 2, yy, 5, E(.6), .45)
                continue
            if wrong:
                draw_bitmap(cv, Bitmap(CROSS, x + sw / 2 - .5, yy, 1.0), A(.6), fade)
                cv.rect(x + sw / 2 - .5, yp, sw - 2, 3.0, A(.62) if not cur else A(.8), fade)
                if cur: cv.glow(x + sw / 2, yp, 7, A(.7), .7)
                continue
            col = E(.8) if cur else pal.ramp("energy", .32)
            cv.rect(x + sw / 2 - .5, yy, sw - 2, 3.0, col, fade)
            if cur: cv.glow(x + sw / 2, yy, 7, E(.8), .7)
        cv.line(px0, top - 3, px0, top + nl * lh + 3, 1.0, E(.85), 1.0)


# ===================================================================== Laplace's demon over a billiard table
EYE_MARK = None


def draw_eye(cv, pal, x, y, r, look=(0.0, 0.0), blink=0.0, alpha=1.0):
    """A hayret-style eye: almond cream with türkuaz iris and coral pupil that looks toward `look` (unit-ish vector);
    blink ∈ [0,1] closes the lids. r = half-width in world units."""
    E, A = pal.ramp("energy", .7), pal.ramp("accent", .55)
    h = r * .62 * (1 - blink)
    if h < .5:
        cv.line(x - r, y, x + r, y, 1.0, pal.ramp("pale", .9), alpha); return
    pts = [(x + r * math.cos(t), y + h * math.sin(t) * (1 if math.sin(t) > 0 else 1)) for t in np.linspace(0, TAU, 20)]
    cv.poly(pts, _hex("#060814"), alpha)
    inner = [(x + (r - .9) * math.cos(t), y + max(.1, h - .9) * math.sin(t)) for t in np.linspace(0, TAU, 20)]
    cv.poly(inner, _hex("#F4ECDC"), alpha)
    lx, ly = max(-1, min(1, look[0])), max(-1, min(1, look[1]))
    ix, iy = x + lx * r * .35, y + ly * h * .3
    cv.disc(ix, iy, min(r * .5, h * .9), E, alpha)
    cv.disc(ix, iy, min(r * .24, h * .5), A, alpha)
    cv.disc(ix - r * .15, iy - h * .3, max(.5, r * .09), _hex("#D2FFF5"), alpha)


class LaplaceDemon(Scene):
    """Laplace's demon: a many-eyed dark cobalt creature (eyes = hayret eyes whose pupils track the balls, blinking on
    seeded beats) leaning over a billiard table in the lower third. The table runs a real deterministic elastic
    simulation (seeded, pre-rolled `preroll` beats so frame 0 is mid-motion). `paths`: every `path_reveal_every` beats
    one more ball shows its future (next `path_beats`) as a dotted türkuaz line from the SAME simulation, so the ball
    then rolls exactly along it. Collisions → tick SFX on the nearest 16th. `abacus`: beads slide on beats."""
    defaults = {"balls": 7, "paths": True, "eyes": 9, "path_reveal_every": 1.0, "path_beats": 2.0, "abacus": True,
                "preroll": 4.0, "speed": .85, "demon_y": -10.0, "table_top": 62.0, "table_bot": 150.0, "sim_seed": 11}
    TW, TH = 2.0, 1.15            # table interior (physics units)

    def setup(self):
        if self.p.get("chaos_twin"):
            return self._twin_setup()
        p = self.p; rng = np.random.default_rng(p["sim_seed"])
        n = int(p["balls"]); R = .09
        pos = []
        while len(pos) < n:
            c = np.array([rng.uniform(-self.TW / 2 + R, self.TW / 2 - R), rng.uniform(R, self.TH - R)])
            if all(np.hypot(*(c - q)) > 2.4 * R for q in pos): pos.append(c)
        pos = np.array(pos); ang = rng.uniform(0, TAU, n)
        vel = np.stack([np.cos(ang), np.sin(ang)], 1) * p["speed"] * rng.uniform(.6, 1.2, (n, 1))
        self.R = R; self.dt = 1 / 240
        steps = int((p["preroll"] + 40.0) / self.dt)
        self.traj = np.zeros((steps, n, 2)); self.hits = []
        for k in range(steps):
            pos = pos + vel * self.dt
            for d, lo, hi in ((0, -self.TW / 2 + R, self.TW / 2 - R), (1, R, self.TH - R)):
                m = (pos[:, d] < lo) | (pos[:, d] > hi)
                if m.any():
                    vel[m, d] *= -1; pos[:, d] = np.clip(pos[:, d], lo, hi); self.hits.append(k * self.dt - p["preroll"])
            for i in range(n):
                for j in range(i + 1, n):
                    dv = pos[i] - pos[j]; dist = math.hypot(*dv)
                    if dist < 2 * R and np.dot(vel[i] - vel[j], dv) < 0:
                        nrm = dv / dist; rel = np.dot(vel[i] - vel[j], nrm)
                        vel[i] -= rel * nrm; vel[j] += rel * nrm; self.hits.append(k * self.dt - p["preroll"])
            self.traj[k] = pos
        self.blink_beats = sorted(set(int(b) for b in rng.integers(0, 40, 24)))
        self.eye_xy = self._eye_layout(rng)

    # ------------------------------------------------------------------ chaos twins (Sinai billiard)
    TWIN = {"dx": 1e-4, "diverge_at": 3.0, "split_px": 1.0, "bumper_every": 1.5, "bumper_r": .075, "launch": [-.62, .42, .32],
            "readout": True}

    def _twin_sim(self, eps, bumpers, steps):
        """two balls (no ball–ball contact: they are the same ball in two worlds), elastic walls + round bumpers.
        → traj (steps, 2, 2), bumper-hit times of ball 0"""
        R, dt = self.R, self.dt; ux, uy, ang = self.tw_launch
        pos = np.array([[ux, uy], [ux + eps * math.cos(ang + 1.3), uy + eps * math.sin(ang + 1.3)]])
        vel = np.array([[math.cos(ang), math.sin(ang)]] * 2) * self.p["speed"]
        tr = np.zeros((steps, 2, 2)); hits = []
        lo_ = np.array([-self.TW / 2 + R, R]); hi_ = np.array([self.TW / 2 - R, self.TH - R])
        for k in range(steps):
            for i in range(2):                       # exact (sub-step) reflections: no dt-sized discretisation jumps
                p0 = pos[i].copy(); v = vel[i].copy(); rem = dt
                for _ in range(4):
                    best = (rem, None)
                    for bi, (bx, by, br) in enumerate(bumpers):
                        c = np.array([bx, by]); d = p0 - c; rr = R + br
                        A = v @ v; Bq = 2 * d @ v; C = d @ d - rr * rr
                        disc = Bq * Bq - 4 * A * C
                        if disc > 0 and Bq < 0:
                            sh = (-Bq - math.sqrt(disc)) / (2 * A)
                            if -1e-12 <= sh < best[0]: best = (max(sh, 0.0), ("b", c))
                    for d_ in (0, 1):
                        if v[d_] < 0 and p0[d_] + v[d_] * rem < lo_[d_]:
                            sh = (lo_[d_] - p0[d_]) / v[d_]
                            if sh < best[0]: best = (max(sh, 0.0), ("w", d_))
                        if v[d_] > 0 and p0[d_] + v[d_] * rem > hi_[d_]:
                            sh = (hi_[d_] - p0[d_]) / v[d_]
                            if sh < best[0]: best = (max(sh, 0.0), ("w", d_))
                    sh, ev = best
                    p0 = p0 + v * sh; rem -= sh
                    if ev is None: break
                    if ev[0] == "w": v[ev[1]] *= -1
                    else:
                        n_ = (p0 - ev[1]); n_ /= np.linalg.norm(n_); v = v - 2 * (v @ n_) * n_
                        if i == 0: hits.append(k * dt + (dt - rem))
                pos[i] = p0; vel[i] = v
            tr[k] = pos
        return tr, hits

    def _twin_setup(self):
        p = self.p; tw = {**self.TWIN, **(p["chaos_twin"] if isinstance(p["chaos_twin"], dict) else {})}
        self.tw = tw; self.R = .09; self.dt = 1 / 240; self.tw_launch = tuple(tw["launch"])
        rng = np.random.default_rng(p["sim_seed"])
        steps = int(max(self.dur, 12.0) / self.dt) + 2
        # bumpers placed one by one so ball A grazes one every `bumper_every` beats (the one at diverge_at matters)
        bumpers = []; br = tw["bumper_r"]
        for k in range(1, 12):
            th = k * tw["bumper_every"]
            if th > max(self.dur, 9.0) - .3: break
            tr, _ = self._twin_sim(0.0, bumpers, int((th + .01) / self.dt) + 2)
            q = tr[int(th / self.dt), 0]; v = (tr[int(th / self.dt), 0] - tr[int(th / self.dt) - 1, 0]); v /= np.linalg.norm(v)
            for side, deg in [(sd, dg) for dg in (48, 40, 56, 34) for sd in ((-1, 1) if k % 2 else (1, -1))]:
                a = math.atan2(v[1], v[0]) + side * math.radians(deg)
                c = q + (self.R + br) * np.array([math.cos(a), math.sin(a)])
                ok = (-self.TW / 2 + .16 < c[0] < self.TW / 2 - .16) and (.16 < c[1] < self.TH - .16)
                ok = ok and all(np.hypot(c[0] - b[0], c[1] - b[1]) > 2.5 * (br + self.R) for b in bumpers)
                past = tr[:int(th / self.dt) - 4, 0]
                ok = ok and (len(past) == 0 or np.hypot(*(past - c).T).min() > self.R + br + .01)
                if ok: bumpers.append((float(c[0]), float(c[1]), br)); break
        self.bumpers = bumpers
        # bisection on log(eps): the twins separate by `split_px` art px exactly at diverge_at
        def t_split(eps):
            tr, _ = self._twin_sim(eps, bumpers, steps)
            X, Y, _s = self._tw(tr); g = np.hypot(X[:, 0] - X[:, 1], Y[:, 0] - Y[:, 1])
            k = np.nonzero(g > tw["split_px"])[0]; return (k[0] * self.dt if len(k) else 1e9), tr
        lo, hi = math.log(1e-14), math.log(5e-2)
        for _ in range(40):
            mid = (lo + hi) / 2; t, _ = t_split(math.exp(mid))
            if t > tw["diverge_at"]: lo = mid
            else: hi = mid
        self.eps = math.exp(hi); self.t_split, self.traj = t_split(self.eps)
        _, self.hits = self._twin_sim(self.eps, bumpers, steps)
        self.blink_beats = sorted(set(int(b) for b in rng.integers(0, 40, 24)))
        self.eye_xy = self._eye_layout(rng)

    def _twin_at(self, lb):
        k = int(round(lb / self.dt)); return self.traj[max(0, min(len(self.traj) - 1, k))]

    def _twin_draw(self, cv, lt, lb):
        p, pal, E = self.p, self.pal, self.E
        recent = [h for h in self.hits if 0 <= lb - h < .5]
        for bx, by, br in self.bumpers:                       # bumper posts: violet ring, gold cap, flash when hit
            X, Y, S = self._tw(np.array([bx, by])); X, Y = float(X), float(Y); r = br / (self.TW / 2) * 62 * float(S)
            hit = 0.0
            for h in recent:
                q = self._twin_at(h)[0]
                if math.hypot(q[0] - bx, q[1] - by) < self.R + br + .02: hit = max(hit, 1 - (lb - h) / .5)
            cv.ellipse(X + 1, Y + r * .7, r * 1.1, r * .5, _hex("#060814"), .7)
            cv.disc(X, Y + r * .25, r, pal.ramp("body", .35), 1.0)
            cv.disc(X, Y, r, pal.ramp("body", .75 + .25 * hit), 1.0)
            cv.disc(X, Y, r * .55, pal.ramp("energy", .55 + .4 * hit), 1.0)
            cv.disc(X - r * .2, Y - r * .25, max(.5, r * .22), pal.ramp("energy", 1.0), .9)
            if hit > 0: cv.glow(X, Y, r * 3, pal.ramp("energy", .8), .45 * hit); cv.ring(X, Y, r * (1.2 + 1.2 * (1 - hit)), .5, pal.ramp("energy", .9), hit)
        cols = (_hex("#41E8D2"), _hex("#FF9A86"))
        ks = np.arange(0, int(p["path_beats"] / self.dt), int(.0625 / self.dt))
        fut = np.array([self._twin_at(lb + k * self.dt) for k in ks])              # (n, 2, 2)
        X, Y, S = self._tw(fut)
        gap = np.hypot(X[:, 0] - X[:, 1], Y[:, 0] - Y[:, 1])
        for j in range(1, len(ks)):
            if (j // 2) % 2: continue                                               # dashes
            a = (1 - j / len(ks))
            if gap[j] < 1.0:
                cv.line(float(X[j - 1, 0]), float(Y[j - 1, 0]), float(X[j, 0]), float(Y[j, 0]), .8, pal.ramp("pale", .9), min(1, a * 1.4))
            else:
                for i in (1, 0):
                    cv.line(float(X[j - 1, i]), float(Y[j - 1, i]), float(X[j, i]), float(Y[j, i]), .8, cols[i], min(1, a * 1.4))
        now = self._twin_at(lb); X, Y, S = self._tw(now)
        g = math.hypot(X[0] - X[1], Y[0] - Y[1])
        if g >= 1.0: cv.line(float(X[0]), float(Y[0]), float(X[1]), float(Y[1]), .6, pal.ramp("accent", .7), .9)
        for i in (1, 0):
            r = self.R / (self.TW / 2) * 62 * S[i]
            cv.ellipse(float(X[i]) + 1, float(Y[i]) + r * .7, r, r * .45, _hex("#060814"), .6)
            cv.disc(float(X[i]), float(Y[i]), r, cols[i], 1.0)
            cv.disc(float(X[i]) - r * .35, float(Y[i]) - r * .35, max(.6, r * .3), _hex("#F4ECDC"), .9)
        if self.tw.get("readout"):
            from .minifont import draw_mini
            gp = float(np.hypot(*(now[0] - now[1]))) / self.eps * self.tw["dx"]
            txt = "FARK " + (("%.4f" % gp) if gp < .01 else ("%.3f" % gp) if gp < 1 else ("%.2f" % gp)).replace(".", ",")
            draw_mini(cv, txt, -52.0, p["table_top"] - 13.0, 1.0, pal.ramp("accent", .75) if g >= 1 else pal.ramp("pale", .8), 1.0)

    def _eye_layout(self, rng):
        n = int(self.p["eyes"]); out = [(0.0, -4.0, 12.0)]
        for i in range(1, n):
            a = (i - 1) / (n - 1) * TAU - math.pi / 2 + .35; rr = 27 + 5 * (i % 2)
            out.append((rr * math.cos(a) * 1.3, rr * math.sin(a) * .72 - 6, 6.2 + 1.4 * ((i * 7) % 3) / 2))
        return out

    def _at(self, lb):
        k = int(round((lb + self.p["preroll"]) / self.dt)); return self.traj[max(0, min(len(self.traj) - 1, k))]

    def _tw(self, q):
        """physics (u, v) → world (x, y) on the trapezoid table"""
        p = self.p; v = q[..., 1] / self.TH
        y = p["table_top"] + (p["table_bot"] - p["table_top"]) * v
        half = 60 + 16 * v
        return q[..., 0] / (self.TW / 2) * half, y, .8 + .45 * v          # x, y, scale

    def focus(self, lb, dur_b):
        return 0.0, self.p["demon_y"]

    def sfx(self, dur_b):
        q = sorted(set(round(round(h * 4) / 4, 3) for h in self.hits if 0 <= h < dur_b))
        return [(b, "tick") for b in q[:24]]

    def draw(self, cv, lt, lb, dur_b):
        p, pal, E, A = self.p, self.pal, self.E, self.A
        self._table(cv, lt, lb)
        self._demon(cv, lt, lb)
        if p["abacus"]: self._abacus(cv, lb)
        if p.get("chaos_twin"): self._twin_draw(cv, lt, lb)
        else: self._balls(cv, lt, lb)

    def _table(self, cv, lt, lb):
        p, pal = self.p, self.pal
        t, b = p["table_top"], p["table_bot"]
        rim = [(-70, t - 8), (70, t - 8), (88, b + 9), (-88, b + 9)]
        cv.poly([(x, y + 6) for x, y in rim], pal.ramp("bg", .05), 1.0)                     # shadow
        cv.poly(rim, _hex("#7E1F35"), 1.0)                                                   # wooden rail (Kiremit)
        cv.poly([(-66, t - 4), (66, t - 4), (83, b + 5), (-83, b + 5)], _hex("#F4ECDC"), 1.0)   # cream cushion
        felt = [(-62, t - 1), (62, t - 1), (78, b + 2), (-78, b + 2)]
        cv.poly(felt, _hex("#0B4F5C"), 1.0)
        cv.poly([(-50, t + 6), (50, t + 6), (62, b - 6), (-62, b - 6)], _hex("#13A39B"), .18)
        for x, y in ((-63, t - 2), (63, t - 2), (-71, (t + b) / 2), (71, (t + b) / 2), (-80, b + 4), (80, b + 4)):
            cv.disc(x, y, 3.2, _hex("#060814"), 1.0)                                         # pockets
        cv.matte(0, (t + b) / 2, 150, b - t, .5)

    def _balls(self, cv, lt, lb):
        p, pal, E, A = self.p, self.pal, self.E, self.A
        cols = [_hex(c) for c in ("#F4ECDC", "#EC4A57", "#41E8D2", "#4169D1", "#FF9A86", "#B8CDF2", "#13A39B")]
        now = self._at(lb)
        if p["paths"]:
            shown = min(len(now), 1 + int(max(0.0, lb) // p["path_reveal_every"]))
            ks = np.arange(0, int(p["path_beats"] / self.dt), int(.0625 / self.dt))
            for i in range(shown):
                fut = np.array([self._at(lb + k * self.dt)[i] for k in ks])
                X, Y, S = self._tw(fut)
                fresh = 1.0 if i == shown - 1 else .55
                for j in range(1, len(X), 1):
                    if j % 2: continue
                    a = (1 - j / len(X)) * fresh
                    cv.disc(float(X[j]), float(Y[j]), 1.1 * float(S[j]), E(.9), min(1, a * 1.3))
                cv.disc(float(X[-1]), float(Y[-1]), 1.6, E(.7), .6 * fresh)
        X, Y, S = self._tw(now)
        order = np.argsort(Y)
        for i in order:
            r = self.R / (self.TW / 2) * 62 * S[i]
            cv.ellipse(float(X[i]) + 1, float(Y[i]) + r * .7, r, r * .45, _hex("#060814"), .6)
            cv.disc(float(X[i]), float(Y[i]), r, cols[i % len(cols)], 1.0)
            cv.disc(float(X[i]) - r * .35, float(Y[i]) - r * .35, max(.6, r * .3), _hex("#F4ECDC"), .9)
            if i == 0: cv.glow(float(X[i]), float(Y[i]), 6, E(.5), .25)

    def _demon(self, cv, lt, lb):
        p, pal, E, A = self.p, self.pal, self.E, self.A
        cx, cy = 0.0, p["demon_y"]
        # body: wobbly blob + two arms resting on the rail
        pts = []
        for t in np.linspace(0, TAU, 48, endpoint=False):
            r = 50 + 3.5 * math.sin(3 * t + lt * 1.3) + 2.5 * math.sin(5 * t - lt * .9)
            pts.append((cx + r * 1.15 * math.cos(t), cy + r * .78 * math.sin(t)))
        cv.glow(cx, cy, 70, pal.ramp("body", .45), .25)
        for s in (-1, 1):
            arm = [(cx + s * 30, cy + 22), (cx + s * 50, cy + 40), (cx + s * 56, p["table_top"] - 6),
                   (cx + s * 44, p["table_top"] - 6), (cx + s * 36, cy + 42), (cx + s * 18, cy + 30)]
            cv.poly(arm, _hex("#1E2E73"), 1.0)
            for f in range(3):
                cv.disc(cx + s * (45 + f * 4.5), p["table_top"] - 5, 2.4, _hex("#2C47A6"), 1.0)
        cv.poly(pts, _hex("#141E4A"), 1.0)
        cv.poly([(x * .97 + cx * .03, y * .97 + cy * .03 - 1) for x, y in pts], _hex("#1E2E73"), 1.0)
        cv.poly_outline(pts, _hex("#4169D1"), 1.0)
        # horns (tiny, friendly)
        for s in (-1, 1):
            cv.poly([(cx + s * 26, cy - 30), (cx + s * 36, cy - 44), (cx + s * 33, cy - 28)], _hex("#2C47A6"), 1.0)
        # a small friendly grin under the big eye (coral, two teeth)
        gy = cy + 27
        cv.poly([(cx - 11, gy), (cx + 11, gy), (cx + 7, gy + 5), (cx - 7, gy + 5)], _hex("#7E1F35"), 1.0)
        cv.line(cx - 11, gy, cx + 11, gy, 1.0, _hex("#EC4A57"), 1.0)
        for tx_ in (-4, 4): cv.rect(cx + tx_, gy + 1.5, 2.2, 2.4, _hex("#F4ECDC"), 1.0)
        # eyes look at balls
        now = self._twin_at(lb) if p.get("chaos_twin") else self._at(lb); X, Y, _ = self._tw(now)
        for i, (ex, ey, er) in enumerate(self.eye_xy):
            x, y = cx + ex, cy + ey
            tx, ty = float(X[i % len(X)]), float(Y[i % len(Y)])
            d = math.hypot(tx - x, ty - y) or 1
            gbi = int(math.floor(self.gbeat(lb) + i * .37))
            bl = 0.0
            if (gbi + i) % 40 in self.blink_beats:
                ph = (self.gbeat(lb) + i * .37) % 1.0
                if ph < .2: bl = math.sin(ph / .2 * math.pi)
            draw_eye(cv, pal, x, y, er, ((tx - x) / d, (ty - y) / d), bl)
        cv.glow(cx, cy - 4, 18, E(.6), .1 + .15 * pulse(lb, 1.0, 4))

    def _abacus(self, cv, lb):
        pal = self.pal
        x0, y0, w, h = 66.0, -10.0, 18.0, 40.0
        cv.rect(x0, y0, w + 4, h + 4, _hex("#7E1F35"), 1.0)
        cv.rect(x0, y0, w, h, _hex("#0B1230"), 1.0)
        for r in range(5):
            y = y0 - h / 2 + 5 + r * 7.5
            cv.line(x0 - w / 2, y, x0 + w / 2, y, .8, pal.ramp("pale", .5), 1.0)
            n = int(math.floor(lb + r * 1.7)) % 5          # beads slide on beats
            for k in range(4):
                left = k < n
                fx = (x0 - w / 2 + 2.5 + k * 3.2) if left else (x0 + w / 2 - 2.5 - (3 - k) * 3.2)
                col = _hex("#41E8D2") if (r == int(lb) % 5 and left) else _hex("#F4ECDC")
                cv.ellipse(fx, y, 1.5, 1.8, col, 1.0)


# ===================================================================== dominoes before a pendulum clock
PIPS = {0: [], 1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
        5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}


def draw_domino(cv, pal, bx, by, s, ang, pips=(3, 5), eyes="closed", look=0.0, glow=0.0, alpha=1.0, side=1):
    """A cartoon domino standing on its base point (bx, by): cream face (w 10, h 20 world × s) with an ink outline,
    a Sis thickness strip, top half = face (eyes 'closed' | 'open' | 'none'), bottom half = pips. ang = screen-plane
    tilt in radians (+ = falls to the right) about the bottom corner on the falling side."""
    w, h, t = 10 * s, 20 * s, 3 * s
    piv = (bx + (w / 2 if ang >= 0 else -w / 2), by)
    c, sn = math.cos(ang), math.sin(ang)

    def P(x, y):           # local (x right, y up from base centre) → world, rotated about the pivot
        X, Y = bx + x - piv[0], by - y - piv[1]
        return (piv[0] + X * c - Y * sn, piv[1] + X * sn + Y * c)
    sd = side * t
    body = [P(-w / 2, 0), P(w / 2, 0), P(w / 2, h), P(-w / 2, h)]
    thick = [P(w / 2 * side, 0), P(w / 2 * side + sd, .35 * t), P(w / 2 * side + sd, h + .35 * t), P(w / 2 * side, h)]
    cv.poly(thick, _hex("#77A2EE"), alpha)
    cv.poly(body, _hex("#F4ECDC"), alpha)
    cv.poly_outline(body, _hex("#060814"), alpha)
    if glow > 0: cv.glow(*P(0, h / 2), 10 * s, pal.ramp("energy", .7), glow)
    a_, b_ = P(-w / 2 + 1.2 * s, h / 2), P(w / 2 - 1.2 * s, h / 2)
    cv.line(a_[0], a_[1], b_[0], b_[1], max(.7, .6 * s), _hex("#141E4A"), alpha)
    ink = _hex("#060814")
    for half, v in ((0, pips[1]),):
        for px, py in PIPS[int(v) % 7]:
            q = P(px * w * .27, h * .25 - py * h * .12)
            cv.disc(q[0], q[1], max(.55, .75 * s), ink, alpha)
    ey = h * .72
    if eyes == "closed":
        for ex in (-1, 1):
            q0, q1 = P(ex * w * .22 - 1.1 * s, ey), P(ex * w * .22 + 1.1 * s, ey)
            cv.line(q0[0], q0[1], q1[0], q1[1], max(.7, .6 * s), ink, alpha)
    elif eyes == "open":
        for ex in (-1, 1):
            q = P(ex * w * .22, ey)
            cv.ellipse(q[0], q[1], 1.9 * s, 2.2 * s, ink, alpha)
            cv.ellipse(q[0], q[1], 1.5 * s, 1.8 * s, _hex("#FFFFFF"), alpha)
            p2 = P(ex * w * .22 + look * .9 * s, ey)
            cv.disc(p2[0], p2[1], max(.7, 1.05 * s), ink, alpha)
        bq = P(0, h * .55)
        cv.disc(bq[0], bq[1], max(.5, .55 * s), _hex("#EC4A57"), alpha)        # tiny coral mouth


class Dominoes(Scene):
    """A domino run: `n` dominoes on a perspective line from the far right into the lower-left foreground; one topples
    every `fall_every` beats (4-frame fall + tick SFX), `preroll_down` already fallen at frame 0. A big pendulum clock
    behind (cream glyph-tick numerals, 2-beat pendulum, hands step on beats). `hero`: the hooded hero waits at the end of
    the line (the chain comes for him). `split`: two halves (coral divider): top 'hard' = closed-eye dominoes falling
    mechanically, bottom 'thinker' = at `thinker_at` one domino opens its eyes, looks left/right, then chooses a side
    branch (türkuaz light) instead of the next domino."""
    defaults = {"n": 24, "fall_every": 0.5, "clock": True, "pendulum": True, "perspective": True, "split": False,
                "top": "hard", "bottom": "thinker", "thinker_at": 3.0, "preroll_down": 4, "hero": True,
                "clock_x": 30.0, "clock_y": -28.0, "clock_r": 30.0, "ground_y": 60.0, "fall_beats": .27, "case_w": 112.0,
                "split_k": 5}

    def _fallen(self, i, lb, start=0):
        """tilt progress 0..1 of domino i (i = 0 falls first)."""
        p = self.p; t0 = (i - p["preroll_down"] - start) * p["fall_every"]
        return min(1.0, max(0.0, (lb - t0) / p["fall_beats"]))

    def sfx(self, dur_b):
        p = self.p; out = []
        for i in range(int(p["n"])):
            b = (i - p["preroll_down"]) * p["fall_every"] + p["fall_beats"]
            if 0 <= b < dur_b: out.append((round(b * 4) / 4, "tick"))
        if p["split"]: out.append((p["thinker_at"], "pop"))
        return out

    def focus(self, lb, dur_b):
        if self.p["split"]: return 0.0, 80.0
        return -40.0, 100.0

    def draw(self, cv, lt, lb, dur_b):
        p = self.p
        if p["split"]: return self._split(cv, lt, lb)
        if p["clock"]: self._clock(cv, lt, lb)
        self._ground(cv)
        self._run(cv, lt, lb)

    def _ground(self, cv):
        pal = self.pal; gy = self.p["ground_y"]
        cv.mask_fill(lambda x, y: y > gy, pal.ramp("bg", .5), 1.0)
        for i in range(8):
            yy = gy + 2 + (i ** 1.7) * 3.6
            cv.line(-120, yy, 120, yy, .7, pal.ramp("bg", .9), .5)

    def _path(self, z):
        """z = 0 near (lower-left, next to the hero) … 1 far (back, by the clock): a cubic Bézier S-curve so the faces
        stay separate instead of stacking into a wall. → (x, y, scale)"""
        P = [(-44, 146), (60, 140), (88, 92), (-6, self.p["ground_y"] + 8)]
        u = 1 - z
        x = u**3 * P[0][0] + 3 * u * u * z * P[1][0] + 3 * u * z * z * P[2][0] + z**3 * P[3][0]
        y = u**3 * P[0][1] + 3 * u * u * z * P[1][1] + 3 * u * z * z * P[2][1] + z**3 * P[3][1]
        return x, y, 1.45 * (1 - z) ** 1.1 + .5

    def _run(self, cv, lt, lb):
        p, pal, E, A = self.p, self.pal, self.E, self.A
        n = int(p["n"])
        pts = [self._path(1 - i / (n - 1)) for i in range(n)]       # i = 0 is the farthest (falls first)
        items = []
        for i in range(n):
            x, y, s = pts[i]
            nx = pts[i + 1][0] if i + 1 < n else x - 10
            d = 1 if nx > x else -1                                  # topple toward the next (nearer) domino
            f = self._fallen(i, lb)
            ang = d * 1.2 * ease(f, "inCubic")
            items.append((y, i, x, s, ang, f, d))
        for y, i, x, s, ang, f, d in sorted(items):
            cv.ellipse(x + d * 3 * s, y + 1, 7 * s, 2 * s, _hex("#060814"), .6)
            just = 0 < f < 1
            draw_domino(cv, pal, x, y, s, ang, pips=(i % 7, (i * 3 + 1) % 7), eyes="closed", side=-d,
                        glow=.5 if just else 0.0)
            if just: cv.glow(x + d * 6 * s, y - 4 * s, 8 * s, E(.7), .5)
        if p["hero"]:
            k = sum(1 for i in range(n) if self._fallen(i, lb) >= 1) / n
            fr = HERO["look_r"] if k < .72 else HERO["wow"]
            if 2.9 < (lb % 3.1) < 3.05: fr = HERO["blink"]
            draw_sprite(cv, fr, -70, 152, 2.2)

    def _clock(self, cv, lt, lb):
        """grandfather clock standing on the ground behind the run; plate-prop slot (≤ `case_w` wide) between face and
        pendulum window at (clock_x, clock_y + clock_r + 15)."""
        p, pal, E, A = self.p, self.pal, self.E, self.A
        cx, cy, R, gy = p["clock_x"], p["clock_y"], p["clock_r"], p["ground_y"]
        top, w = cy - R - 6, max(2 * R + 14, p["case_w"])
        cv.rect(cx, (top + gy) / 2, w + 4, gy - top, _hex("#0B1230"), 1.0)
        cv.rect(cx, (top + gy) / 2, w, gy - top - 2, _hex("#1E2E73"), 1.0)
        cv.matte(cx, (top + gy) / 2, w + 4, gy - top, .85)                                         # no ray bloom on the cabinet
        cv.line(cx - w / 2 + 2, top + 2, cx - w / 2 + 2, gy - 2, 1, _hex("#4169D1"), 1.0)          # lit edge
        wy0, wy1 = cy + R + 23, gy - 5
        cv.rect(cx, (wy0 + wy1) / 2, 30, wy1 - wy0, _hex("#060814"), 1.0)                        # pendulum window
        if p["pendulum"]:
            ang = math.radians(14) * math.sin(lb * math.pi)                                         # 2-beat period
            L = wy1 - cy - 6
            bx, by = cx + L * math.sin(ang), cy + L * math.cos(ang)
            k = (by - wy0) / max(1.0, L)
            sx, sy = cx + (wy0 - cy) * math.tan(ang), wy0
            cv.line(sx, sy, bx, by, 1.2, _hex("#B8CDF2"), 1.0)
            cv.disc(bx, by, 6, _hex("#FF9A86"), 1.0); cv.disc(bx, by, 4.5, _hex("#EC4A57"), 1.0)
            cv.disc(bx - 1.5, by - 1.5, 1.4, _hex("#F4ECDC"), 1.0)
            cv.glow(bx, by, 11, A(.6), .2 + .25 * pulse(lb, 1.0, 5))
        cv.disc(cx, cy, R + 4, _hex("#7E1F35"), 1.0)
        cv.disc(cx, cy, R + 1.5, _hex("#F4ECDC"), 1.0)
        cv.disc(cx, cy, R, _hex("#2C47A6"), 1.0)
        cv.ring(cx, cy, R - 6, 1, _hex("#4169D1"), 1.0)
        for k in range(12):                                   # glyph numerals: bars, double bars on the quarters
            a = k / 12 * TAU
            r0, r1 = R - 8, R - 2
            for j in ((-1.1, 1.1) if k % 3 == 0 else (0,)):
                ox, oy = j * math.cos(a), j * math.sin(a)
                cv.line(cx + r0 * math.sin(a) + ox, cy - r0 * math.cos(a) + oy, cx + r1 * math.sin(a) + ox,
                        cy - r1 * math.cos(a) + oy, 1.5, _hex("#F4ECDC"), 1.0)
        sa = math.floor(lb) / 12 * TAU; ma = lb / 32 * TAU + 1.0
        cv.line(cx, cy, cx + .5 * R * math.sin(ma), cy - .5 * R * math.cos(ma), 2.6, _hex("#F4ECDC"), 1.0)
        cv.line(cx, cy, cx + .78 * R * math.sin(sa), cy - .78 * R * math.cos(sa), 1.3, _hex("#EC4A57"), 1.0)
        cv.disc(cx, cy, 2.6, _hex("#EC4A57"), 1.0)

    # ---------- split: hard (top) vs thinker (bottom)
    def _split(self, cv, lt, lb):
        p, pal, E, A = self.p, self.pal, self.E, self.A
        cv.mask_fill(lambda x, y: (y > -6) & (y < 8), pal.ramp("bg", .3), 1.0)
        cv.mask_fill(lambda x, y: y >= 8, pal.ramp("bg", .45), 1.0)
        cv.line(-120, 8, 120, 8, 1.6, _hex("#EC4A57"), 1.0); cv.glow(0, 8, 30, A(.6), .2)
        n = int(p["n"]); sp = 17.0
        # top row: an endless mechanical conveyor; the camera tracks the toppling front so it never runs out
        fe = p["fall_every"]; shift = lb / fe * sp; x0 = -60.0
        i0 = int(math.floor((shift - 120 - x0) / sp)); i1 = int(math.ceil((shift + 120 - x0) / sp))
        for i in range(i0, i1 + 1):
            x = x0 + i * sp - shift; f = self._fallen(i, lb)
            ang = 1.15 * ease(f, "inCubic")
            draw_domino(cv, pal, x, -12, 1.3, ang, pips=(i % 7, (i * 3 + 1) % 7), eyes="closed", side=1,
                        glow=.4 if 0 < f < 1 else 0.0)
        # bottom row: the same chain, but the thinker (index k) looks around and hops onto a side branch
        k = int(p["split_k"]); ta = p["thinker_at"]; yb = 70.0; x0 = -84.0
        tx = x0 + k * sp
        for i in range(n):
            if i == k: continue
            x = x0 + i * sp + (8 if i > k else 0)
            if i < k:
                f = self._fallen(i, lb, start=k - p["preroll_down"] - ta / fe)
                draw_domino(cv, pal, x, yb, 1.3, 1.15 * ease(f, "inCubic"), pips=(i % 7, (i * 5 + 2) % 7),
                            eyes="closed", side=1)
            else:
                draw_domino(cv, pal, x, yb, 1.3, 0.0, pips=(i % 7, (i * 5 + 2) % 7), eyes="closed", side=1, alpha=.9)
        chosen = lb >= ta + 2.0
        br = [(tx + 20 + j * 14, yb + 34 + j * 11) for j in range(6)]
        for j, (x, y) in enumerate(br):
            fj = min(1.0, max(0.0, (lb - (ta + 2.75 + j * fe)) / p["fall_beats"]))
            draw_domino(cv, pal, x, y, 1.3 + .05 * j, 1.0 * ease(fj, "inCubic"), pips=(j + 1, (j * 2) % 7),
                        eyes="closed", side=1, glow=(.55 if chosen else 0.0))
            if chosen: cv.glow(x, y - 12, 12, E(.7), .35)
        self._thinker(cv, tx, yb, lb, ta, (br[0][0] - 16, br[0][1] - 2))

    def _thinker(self, cv, x, y, lb, ta, land):
        pal = self.pal; S = 1.9
        if lb < ta:
            draw_domino(cv, pal, x, y, S, 0.0, pips=(6, 6), eyes="closed", side=1); return
        if lb < ta + 2.0:   # eyes open, look left (1 beat) then right (1 beat), tiny startle hop
            look = -1.0 if lb < ta + 1.0 else 1.0
            hop = 3.0 * math.sin((lb - ta) / .3 * math.pi) if lb < ta + .3 else 0.0
            draw_domino(cv, pal, x, y - hop, S, 0.0, pips=(6, 6), eyes="open", look=look, side=1, glow=.5)
            return
        k = min(1.0, (lb - ta - 2.0) / .5)                 # hop onto the branch …
        hx = x + (land[0] - x) * ease(k, "inOutSine"); hy = y + (land[1] - y) * k - 14 * math.sin(k * math.pi)
        f = min(1.0, max(0.0, (lb - ta - 2.5) / .25))       # … then topple along it
        draw_domino(cv, pal, hx, hy, S, .9 * ease(f, "inCubic"), pips=(6, 6), eyes="open", look=1.0, side=1, glow=.6)


# ===================================================================== Libet clock + EEG strip (+ Schurger 2012 noise)
def accumulator_epochs(n_epochs=240, pre_s=4.0, post_s=.6, dt=.005, leak=2.4, drift=.11, noise=.1, seed=7, thr_sd=3.2,
                       max_s=40.0):
    """Schurger-style leaky stochastic accumulator  dx = (I − k·x)dt + c·√dt·ξ, started from its stationary
    distribution; a 'movement' fires at the first threshold crossing after `pre_s`. Returns (u, epochs): epochs are
    time-locked to the crossing (u = 0), followed by a fast post-movement decay, normalised so baseline = 0 and
    threshold = 1. Vectorised over walkers; deterministic for a seed."""
    rng = np.random.default_rng(seed)
    base = drift / leak; sd = noise / math.sqrt(2 * leak); thr = base + thr_sd * sd
    npre, npost, T = int(round(pre_s / dt)), int(round(post_s / dt)), int(round(max_s / dt))
    N = n_epochs * 3
    xs = np.empty((T, N), np.float32); x = base + sd * rng.standard_normal(N)
    a, c = 1 - leak * dt, noise * math.sqrt(dt)
    for i in range(T):
        x = x * a + drift * dt + c * rng.standard_normal(N); xs[i] = x
    above = xs >= thr
    above[:npre] = False
    first = np.where(above.any(0), above.argmax(0), -1)
    out = []
    for j in np.flatnonzero(first > 0):
        if xs[:first[j], j].max() >= thr and (xs[first[j] - npre:first[j], j] >= thr).any(): continue
        pre = xs[first[j] - npre + 1:first[j] + 1, j].astype(float)
        post = base + (pre[-1] - base) * np.exp(-np.arange(1, npost + 1) * dt / .08)
        out.append(np.concatenate([pre, post]))
        if len(out) >= n_epochs: break
    ep = (np.array(out) - base) / (thr - base)
    u = (np.arange(npre + npost) - npre + 1) * dt
    return u, ep


class LibetClock(Scene):
    """Libet's experiment as a machine: a cream clock face (60 ticks) with a coral spot revolving once per `period_s`
    (+ tail); an EEG strip in the lower third (Gece screen, türkuaz trace) that scrolls left until the big button is
    pressed at `press_at`, then freezes time-locked to the press: the readiness potential ramp (negative up, as in
    EEG convention) starting about `rp_onset_ms`, a coral W marker at `w_ms` on the strip and on the clock rim.
    At `noise_at` the single ramp splits (over 1 beat) into `noise_trials` thin noisy single trials from a leaky
    stochastic accumulator (Schurger 2012), while their average (thick) stays: the ramp is what averaging noise
    looks like. Deterministic (seeded), populated at lb 0 (trace pre-rolled)."""
    defaults = {"period_s": 2.56, "rp_onset_ms": -550, "w_ms": -200, "press_at": 3.0, "noise_trials": 12, "noise_at": 4.0,
                "clock_y": -16.0, "clock_r": 41.0, "strip_y": 68.0, "strip_h": 56.0, "window_s": 2.0, "post_s": .4,
                "button_x": -58.0, "button_y": 134.0, "seed": 7}

    def on_bind(self):
        p = self.p
        leak = 1.0 / max(.05, -p["rp_onset_ms"] / 1000 / 1.3)     # time constant ≈ visible ramp onset
        u, ep = accumulator_epochs(n_epochs=240, leak=leak, seed=int(p["seed"]))
        self.u, self.ep = u, ep
        self.avg = ep.mean(0)
        k = max(1, int(.06 / (u[1] - u[0])))
        self.avg_s = np.convolve(np.pad(self.avg, k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), "same")[k:-k]
        self.trials = ep[:int(p["noise_trials"])]

    def sfx(self, dur_b):
        return [(self.p["press_at"], "pop"), (self.p["noise_at"], "glitch")]

    def focus(self, lb, dur_b):
        return (self.p["button_x"], self.p["button_y"]) if lb < self.p["noise_at"] else (0.0, self.p["strip_y"])

    def _tp(self):
        return self.p["press_at"] * .5 * 0 + self.lt_of(self.p["press_at"])

    def lt_of(self, lb):
        return lb * self.spb

    def draw(self, cv, lt, lb, dur_b):
        self.spb = (lt / lb) if lb > 1e-6 else getattr(self, "spb", .5)
        self._clock(cv, lt, lb)
        self._strip(cv, lt, lb)
        self._button(cv, lt, lb)

    def _clock(self, cv, lt, lb):
        p, pal, E, A = self.p, self.pal, self.E, self.A
        cx, cy, R = 0.0, p["clock_y"], p["clock_r"]
        cv.disc(cx + 2, cy + 3, R + 5, _hex("#060814"), .7)
        cv.disc(cx, cy, R + 5, _hex("#2C47A6"), 1.0)
        cv.disc(cx, cy, R + 3, _hex("#141E4A"), 1.0)
        cv.disc(cx, cy, R + 1, _hex("#F4ECDC"), 1.0)
        cv.matte(cx, cy, 1.4 * R, 1.4 * R, .9)
        ink = _hex("#060814")
        for k in range(60):
            a = k / 60 * TAU; L = 6 if k % 5 == 0 else 3
            cv.line(cx + (R - L) * math.sin(a), cy - (R - L) * math.cos(a), cx + (R - 1) * math.sin(a),
                    cy - (R - 1) * math.cos(a), 1.3 if k % 5 == 0 else .8, ink, 1.0)
        per = p["period_s"]
        ang = lambda t: (t / per) % 1.0 * TAU
        tp = self.lt_of(p["press_at"])
        t_now = lt if lb < p["press_at"] + .5 else tp + .25          # the spot keeps turning; after the press it fades
        for j in range(7, -1, -1):
            a = ang(lt - j * .03)
            r = R - 11
            cv.disc(cx + r * math.sin(a), cy - r * math.cos(a), 3.6 - .35 * j, _hex("#EC4A57") if j == 0 else _hex("#FF9A86"),
                    1.0 if j == 0 else .55 - .06 * j)
        if lb >= p["press_at"]:           # W marker: where the spot was at the reported moment of 'wanting'
            aw = ang(tp + p["w_ms"] / 1000)
            k = min(1.0, (lb - p["press_at"]) / .5)
            for dr in (0, 1.2):
                cv.line(cx + (R + 2) * math.sin(aw), cy - (R + 2) * math.cos(aw), cx + (R - 14) * math.sin(aw),
                        cy - (R - 14) * math.cos(aw), 2.2 - dr, _hex("#EC4A57") if dr == 0 else _hex("#FF9A86"), k)
            from .bitmap import draw_text
            al = aw + .44
            wx, wy = cx + (R - 17) * math.sin(al), cy - (R - 15) * math.cos(al)
            cv.disc(wx, wy, 10, _hex("#EC4A57"), k)          # QC: bigger badge + coral ring so the W never touches the edge
            cv.disc(wx, wy, 8.8, _hex("#060814"), k)
            draw_text(cv, "W", wx, wy, 2, _hex("#FF9A86"), k, snap=True)
        cv.disc(cx, cy, 3, ink, 1.0); cv.disc(cx, cy, 1.4, _hex("#EC4A57"), 1.0)

    def _strip(self, cv, lt, lb):
        p, pal, E, A = self.p, self.pal, self.E, self.A
        sy, sh = p["strip_y"], p["strip_h"]; x0, x1 = -84.0, 84.0
        cv.rect(0, sy, x1 - x0 + 6, sh + 6, _hex("#2C47A6"), 1.0)
        cv.rect(0, sy, x1 - x0, sh, _hex("#060814"), 1.0)
        cv.matte(0, sy, x1 - x0, sh, .7)
        for gx in np.arange(x0 + 8, x1, 16): cv.line(gx, sy - sh / 2, gx, sy + sh / 2, .5, _hex("#0B1230"), 1.0)
        for gy in np.arange(sy - sh / 2 + 7, sy + sh / 2, 10): cv.line(x0, gy, x1, gy, .5, _hex("#0B1230"), 1.0)
        tp = self.lt_of(p["press_at"]); W = p["window_s"]
        right = min(lt, tp + p["post_s"])                         # live scroll → frozen, time-locked to the press
        u_r = right - tp
        base_y, amp = sy + sh / 2 - 15, sh - 25                   # negative up (EEG convention)
        X = lambda u: x1 - 2 - (u_r - u) / W * (x1 - x0 - 4)
        uu = self.u
        sel = (uu >= u_r - W) & (uu <= u_r)
        us = uu[sel]
        if not len(us): return
        k = 0.0 if lb < p["noise_at"] else min(1.0, (lb - p["noise_at"]) / 1.0)
        k = ease(k, "outCubic")
        av = self.avg_s[sel]
        jitter = .03 * np.sin(us * 37.0) + .02 * np.sin(us * 61.0 + 1.3)
        if k > 0:
            for i, tr in enumerate(self.trials):
                y = av + jitter * (1 - k) + k * (tr[sel] - av)
                y = np.clip(y, -.45, 1.1)
                pts = [(X(a), base_y - amp * float(b)) for a, b in zip(us[::2], y[::2])]
                col = _hex("#41E8D2") if i % 3 else _hex("#3BC9C0")
                for (ax, ay), (bx, by) in zip(pts, pts[1:]): cv.line(ax, ay, bx, by, .7, col, .55)
        y = av + jitter * (1 - k)
        pts = [(X(a), base_y - amp * float(b)) for a, b in zip(us[::2], y[::2])]
        wdt = 1.4 + 1.2 * k
        for (ax, ay), (bx, by) in zip(pts, pts[1:]): cv.line(ax, ay, bx, by, wdt, _hex("#41E8D2"), 1.0)
        hx, hy = pts[-1]
        if lb < p["press_at"] + p["post_s"] / self.spb:
            cv.disc(hx, hy, 2.2, _hex("#F4ECDC"), 1.0); cv.glow(hx, hy, 8, E(.8), .5)       # pen tip
        for uq, col, w_ in ((p["rp_onset_ms"] / 1000, _hex("#4169D1"), .8), (0.0, _hex("#F4ECDC"), 1.0)):
            if u_r - W < uq <= u_r and (uq != 0.0 or lb >= p["press_at"]):
                xq = X(uq)
                for yy in np.arange(sy - sh / 2 + 2, sy + sh / 2 - 2, 4): cv.line(xq, yy, xq, yy + 2, w_, col, .9)
        if lb >= p["press_at"]:
            xq = X(p["w_ms"] / 1000); kk = min(1.0, (lb - p["press_at"]) / .5)
            cv.line(xq, sy - sh / 2 + 2, xq, sy + sh / 2 - 2, 1.6, _hex("#EC4A57"), kk)
            from .bitmap import draw_text
            cv.rect(xq - 8, sy - sh / 2 + 8, 13, 12, _hex("#060814"), kk)
            draw_text(cv, "W", xq - 8, sy - sh / 2 + 8, 2, _hex("#FF9A86"), kk, snap=True)
        cv.line(x0, base_y, x1, base_y, .5, _hex("#2C47A6"), .8)

    def _button(self, cv, lt, lb):
        p, E, A = self.p, self.E, self.A
        bx, by = p["button_x"], p["button_y"]; pa = p["press_at"]
        down = 1.0 if pa - .05 <= lb < pa + .35 else 0.0
        cv.ellipse(bx, by + 8, 20, 6, _hex("#060814"), .8)
        cv.rect(bx, by + 4, 34, 9, _hex("#1E2E73"), 1.0); cv.ellipse(bx, by + 8, 17, 4, _hex("#141E4A"), 1.0)
        cv.ellipse(bx, by + 1, 17, 6, _hex("#2C47A6"), 1.0)
        top = by - 4 + 3 * down
        cv.ellipse(bx, top + 3, 13, 5, _hex("#7E1F35"), 1.0)
        cv.ellipse(bx, top, 13, 5, _hex("#EC4A57"), 1.0)
        cv.ellipse(bx - 3, top - 1.5, 5, 1.6, _hex("#FF9A86"), 1.0)
        if down: cv.glow(bx, top, 22, A(.8), .6)
        # the finger: approaches over the beat before the press, lifts after
        if lb < pa: f = ease(min(1.0, max(0.0, (lb - (pa - 1.0)) / 1.0)), "inOutSine")
        else: f = 1.0 - ease(min(1.0, max(0.0, (lb - pa - .35) / .6)), "inOutSine")
        fx, fy = bx + 4 - 4 * f, top - 24 + 18 * f                    # fingertip
        cv.line(-100, fy - 16, fx - 7, fy - 9, 11, _hex("#060814"), 1.0)                     # hero's kobalt sleeve
        cv.line(-100, fy - 16, fx - 7, fy - 9, 8.5, _hex("#4169D1"), 1.0)
        cv.line(-100, fy - 19, fx - 8, fy - 12, 1.6, _hex("#77A2EE"), 1.0)
        cv.line(fx - 7, fy - 13, fx - 6, fy - 5, 2, _hex("#F4ECDC"), 1.0)                    # cuff
        cv.disc(fx - 1.5, fy - 7.5, 4.2, _hex("#F4ECDC"), 1.0)                                # mitten hand
        cv.line(fx, fy - 6, fx, fy, 2.6, _hex("#F4ECDC"), 1.0)                                # index finger, down
        cv.line(fx - 4.5, fy - 7, fx - 2, fy - 5, .8, _hex("#B8CDF2"), 1.0)                  # knuckle shade


# ===================================================================== dice → branching futures
DIE_FACES = {(0, 0, 1): 1, (0, 0, -1): 6, (1, 0, 0): 3, (-1, 0, 0): 4, (0, -1, 0): 2, (0, 1, 0): 5}   # opposite sum 7


def _rot(axis, a):
    c, s = math.cos(a), math.sin(a)
    if axis == 0: return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == 1: return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


VIEW = _rot(0, math.radians(-24)) @ _rot(1, math.radians(32))


def draw_die(cv, x, y, size, R, alpha=1.0, glow=0.0, col=None):
    """A real 3-D pixel die (cream body, coral pips, ink edges) under rotation matrix R, viewed slightly from above.
    Visible faces are painted back-to-front with flat lambert shading; pips are projected onto their face."""
    h = size / 2
    M = VIEW @ R
    faces = []
    for n, v in DIE_FACES.items():
        nn = M @ np.array(n, float)
        if nn[2] <= 0.02: continue                               # back-facing (camera looks down −z → +z toward us)
        n0 = np.array(n, float)
        u = np.array([n0[1], n0[2], n0[0]]); w = np.cross(n0, u)
        corners = [n0 * h + (a * u + b * w) * h for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        pts = [(x + (M @ c)[0], y + (M @ c)[1]) for c in corners]
        faces.append((nn[2], pts, v, n0, u, w, nn))
    for z, pts, v, n0, u, w, nn in sorted(faces, key=lambda f: f[0]):
        light = .55 + .45 * max(0.0, float(nn @ np.array([-.4, -.6, .7])))
        # flat palette tones per face (QC: the old cream→mist blend was off-palette and dithered into a bluish checker)
        base = np.array(_hex("#F4ECDC" if light >= .8 else "#B8CDF2" if light >= .62 else "#77A2EE"))
        if col is not None: base = np.array(col) * light
        cv.poly(pts, tuple(base), alpha)
        cv.poly_outline(pts, _hex("#060814"), alpha)
        if col is None and nn[2] > .25:
            for px, py in PIPS[v]:
                c3 = n0 * h * 1.001 + (px * .5 * u + py * .5 * w) * h
                q = M @ c3
                cv.disc(x + q[0], y + q[1], max(.6, size * .085 * (.5 + .5 * nn[2])), _hex("#EC4A57"), alpha)
    if glow > 0: cv.glow(x, y, size, _hex("#FF9A86"), glow)


class FutureTree(Scene):
    """Possible futures as a growing tree of lit paths.
    mode dice: `dice` big 3-D pixel dice tumble mid-air (6-frame quarter-turn every `roll_every` beats, random axis,
      seeded); each landing sprouts a glowing path down into the lower third; a coral countdown ring contracts from
      `ring_countdown_from`; the last `freeze_last` beats are frozen (held breath).
    mode burst: from the dice point a seeded, binary-ish tree grows `depth` generations (one every `grow_every`,
      `pre_gens` already visible at frame 0), 2–3 px paths (widths redrawn per camera zoom, never scaled bitmaps), lamps
      at nodes blinking on 8ths, `walkers` ghost copies of the hero walking different branches (one in full colour on
      the chosen path), and `chosen_path_glow`: one root→leaf path burns türkuaz."""
    defaults = {"mode": "dice", "dice": 2, "roll_every": 0.5, "branch_from_faces": True, "ring_countdown_from": 3.5,
                "freeze_last": 0.5, "depth": 6, "grow_every": 0.5, "pre_gens": 2, "walkers": 8, "chosen_path_glow": True,
                "pull_out": True, "root_y": -34.0, "dice_y": -14.0, "die_size": 30.0, "seed": 11, "spread": 210.0,
                "glow_from": 3.0}

    def on_bind(self):
        p = self.p
        rng = np.random.default_rng(int(p["seed"]))
        self.axes = rng.integers(0, 2, size=(int(p["dice"]), 64))          # tumble axis per roll (x or y)
        self.sgn = rng.choice([-1, 1], size=(int(p["dice"]), 64))
        # tree: node id (g, i), positions
        D = int(p["depth"]); self.nodes = {(0, 0): (0.0, p["root_y"])}
        ys = [p["root_y"]]
        for g in range(1, D + 1): ys.append(ys[-1] + 44 * .86 ** (g - 1))
        for g in range(1, D + 1):
            n = 2 ** g; W = p["spread"] * (g / D) ** .8 * 1.25
            for i in range(n):
                px, py = self.nodes[(g - 1, i // 2)]
                x = -W / 2 + W * (i + .5) / n + float(rng.normal(0, 3.0 / g))
                self.nodes[(g, i)] = (x, ys[g] + float(rng.normal(0, 2.0)))
        self.D = D
        self.chosen = int(rng.integers(0, 2 ** D)) | 0
        leaves = rng.permutation(2 ** D)
        self.walk_leaves = [self.chosen] + [int(l) for l in leaves if int(l) != self.chosen][:max(0, int(p["walkers"]) - 1)]
        self.walk_t0 = [1.0] + [float(rng.uniform(0, 3.0)) for _ in range(len(self.walk_leaves) - 1)]
        self.walk_dur = [9.0] + [float(rng.uniform(5, 9)) for _ in range(len(self.walk_leaves) - 1)]

    def sfx(self, dur_b):
        p = self.p
        if p["mode"] == "dice":
            end = dur_b - p["freeze_last"]
            return [(k * p["roll_every"], "tick") for k in range(int(end / p["roll_every"]) + 1)]
        return [(0, "hit")] + [((g - p["pre_gens"]) * p["grow_every"], "pop") for g in range(p["pre_gens"] + 1, self.D + 1)]

    def focus(self, lb, dur_b):
        return (0.0, self.p["dice_y"]) if self.p["mode"] == "dice" else self.nodes[(0, 0)]

    def draw(self, cv, lt, lb, dur_b):
        if self.p["mode"] == "dice": self._dice(cv, lt, lb, dur_b)
        else: self._burst(cv, lt, lb, dur_b)

    # ---------------------------------------------------------------- dice
    def _orient(self, d, lb):
        """rotation of die d at beat lb: quarter turns accumulated per roll; the current one in 6 quantised frames."""
        re = self.p["roll_every"]; k = int(math.floor(lb / re)); ph = lb / re - k
        R = np.eye(3)
        for j in range(k):
            R = _rot(int(self.axes[d, j % 64]), self.sgn[d, j % 64] * math.pi / 2) @ R
        step = min(6, int(ph * 8)) / 6.0                                  # 6 frames of rotation, then a short rest
        return _rot(int(self.axes[d, k % 64]), self.sgn[d, k % 64] * math.pi / 2 * step) @ R, k, step

    def _top_value(self, R):
        best, v = -9, 1
        for n, val in DIE_FACES.items():
            z = (VIEW @ R @ np.array(n, float))[2]
            if z > best: best, v = z, val
        return v

    def _dice(self, cv, lt, lb, dur_b):
        p, pal, E, A = self.p, self.pal, self.E, self.A
        fz = dur_b - p["freeze_last"]
        lbf = min(lb, fz)
        nd = int(p["dice"]); S = p["die_size"]
        xs = [(-24 + 48 * i / max(1, nd - 1)) if nd > 1 else 0.0 for i in range(nd)]
        y0 = p["dice_y"]
        # ground + sprouting paths (one per completed roll, per die)
        cv.mask_fill(lambda x, y: y > 64, pal.ramp("bg", .45), 1.0)
        re = p["roll_every"]; kmax = int(math.floor(lbf / re))
        if p["branch_from_faces"]:
            for d in range(nd):
                for j in range(kmax - 7, kmax + 1):                     # pre-rolled: older sprouts exist at lb 0
                    age = lbf - j * re
                    if age < 0: continue
                    rng = np.random.default_rng(1000 * d + j + 64)
                    ang = float(rng.uniform(-.9, .9)) + (-.35 if d == 0 else .35)
                    L = min(1.0, age / .4) * float(rng.uniform(70, 120))
                    sx, sy = xs[d], y0 + S * .6
                    pts = [(sx + math.sin(ang) * L * t + 6 * math.sin(t * 5 + j) * t, sy + math.cos(ang) * L * t * 1.1)
                           for t in np.linspace(0, 1, 10)]
                    fade = max(.25, 1 - (kmax - j) * .11)
                    for (a0, b0), (a1, b1) in zip(pts, pts[1:]):
                        cv.line(a0, b0, a1, b1, 2.0, E(.6 * fade + .2), fade)
                    ex, ey = pts[-1]
                    cv.disc(ex, ey, 2.4, E(.9) if j == kmax else E(.55), 1.0)
                    if j == kmax: cv.glow(ex, ey, 10, E(.8), .6)
        # countdown ring
        rc = p["ring_countdown_from"]
        if lbf >= rc:
            k = min(1.0, (lbf - rc) / max(.1, fz - rc))
            r = 86 - 40 * ease(k, "inCubic")
            n_left = max(1, int(math.ceil((fz - lbf) / .5)))
            cv.ring(0, y0, r, 2.2, _hex("#EC4A57"), 1.0, dashes=max(1, n_left * 2), phase=0.0, duty=.7)
            cv.glow(0, y0, r, A(.6), .15 + .2 * pulse(lbf, .5, 6))
        for d in range(nd):
            R, k, step = self._orient(d, lbf)
            bob = 4 * math.sin(lbf * math.pi + d * 1.7)
            hop = -10 * math.sin(step * math.pi) if step < 1 else 0.0
            cv.ellipse(xs[d], 60, S * .55, 3, _hex("#060814"), .5)
            draw_die(cv, xs[d], y0 + bob + hop, S, R, glow=.25 if step >= 1 else .12)

    # ---------------------------------------------------------------- burst
    def _burst(self, cv, lt, lb, dur_b):
        p, pal, E, A = self.p, self.pal, self.E, self.A
        z = cv.cam.zoom
        px_w = lambda n: n / max(.3, z)                                     # constant on-screen width (redrawn)
        ge, pre = p["grow_every"], p["pre_gens"]
        gen = lambda g: min(1.0, max(0.0, (lb - (g - pre - 1) * ge) / ge)) if g > pre else 1.0
        gbt = (self.b0 + lb)
        chosen_path = {(g, self.chosen >> (self.D - g)) for g in range(self.D + 1)}
        lit_to = (lb - p["glow_from"]) / .5 if p["chosen_path_glow"] else -1
        for g in range(1, self.D + 1):                  # not-yet-grown futures: faint dotted ghosts (lower third never empty)
            if gen(g) >= 1: continue
            for i in range(2 ** g):
                x1, y1 = self.nodes[(g, i)]; x0, y0 = self.nodes[(g - 1, i // 2)]
                for t in np.linspace(.1, .95, 8):
                    cv.disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, px_w(1.0), pal.ramp("body", .5), .8)
                cv.disc(x1, y1, px_w(1.6), pal.ramp("body", .55), .9)
        for g in range(1, self.D + 1):
            k = gen(g)
            if k <= 0: continue
            for i in range(2 ** g):
                x1, y1 = self.nodes[(g, i)]; x0, y0 = self.nodes[(g - 1, i // 2)]
                xe, ye = x0 + (x1 - x0) * ease(k, "outCubic"), y0 + (y1 - y0) * ease(k, "outCubic")
                on = (g, i) in chosen_path and g <= lit_to
                mx, my = (x0 + xe) / 2 + (xe - x0) * .15, (y0 + ye) / 2 - 4
                pts = [(x0, y0), (mx, my), (xe, ye)]
                col = E(.9) if on else pal.ramp("body", .62 - .05 * g)
                wd = px_w(3.4 if on else 2.6)
                for (a0, b0), (a1, b1) in zip(pts, pts[1:]): cv.line(a0, b0, a1, b1, wd, col, 1.0)
                if on: cv.glow((x0 + xe) / 2, (y0 + ye) / 2, px_w(10), E(.8), .45)
                if k >= 1:
                    blink = ((g * 7 + i + int(math.floor(gbt * 2))) % 4) == 0
                    cv.disc(x1, y1, px_w(2.0), E(.95) if (blink or on) else pal.ramp("pale", .55), 1.0)
                    if blink: cv.glow(x1, y1, px_w(6), E(.7), .4)
        # root: the two landed dice, small
        rx, ry = self.nodes[(0, 0)]
        cv.glow(rx, ry, px_w(14), A(.6), .4)
        for d, dx in enumerate((-7, 7)):
            R, _, _ = self._orient(d, 13.0)
            draw_die(cv, rx + dx, ry - 6, 10, R)
        # walkers: ghost heroes on different branches; the full-colour one walks the chosen path
        for wi, (leaf, t0, du) in enumerate(zip(self.walk_leaves, self.walk_t0, self.walk_dur)):
            f = (lb - t0) / du
            if f <= 0: continue
            f = min(1.0, f) * self.D
            g = int(math.floor(f)); fr = f - g
            if g >= self.D: g, fr = self.D - 1, 1.0
            a = self.nodes[(g, leaf >> (self.D - g))]; b = self.nodes[(g + 1, leaf >> (self.D - g - 1))]
            if gen(g + 1) < fr: fr = gen(g + 1)
            x, y = a[0] + (b[0] - a[0]) * fr, a[1] + (b[1] - a[1]) * fr
            frame = hero_frame("walk", lb, wi * .3)
            sc = px_w(1.15)
            if wi == 0:
                cv.glow(x, y - px_w(10), px_w(10), E(.8), .2)
                draw_sprite(cv, frame, x, y + px_w(1), sc, flip=b[0] < a[0])
            else: draw_sprite(cv, frame, x, y + px_w(1), sc, flip=b[0] < a[0], alpha=.55)     # ghost: see-through



# ===================================================================== object kind "book" (the legible tag)
BOOK_DEFAULTS = {"state": "closing", "close_at": 0.5, "title": "GELECEĞİN\nKİTABI", "candle": True, "desk": True,
                 "book_w": 120.0, "book_h": 152.0, "book_y": 6.0, "desk_y": 82.0, "dust": 16}


def draw_book(scene, cv, lt, lb, a):
    """Object kind 'book': a thick hardcover standing on a wooden desk by a candle. state 'closing': open at frame 0
    (right page with the big arrow, cracked as at the end of the twist), the cover swings shut at `close_at` (thud).
    Cover: Kobalt leather, cream embossed frame, the eye emblem, the 2-dot snapped `title`, and the publisher line =
    the channel handle in two lines (2 dots, snapped, türkuaz on a matte ink plate, contrast ≈ 14:1) from `brand_at`.
    The cover rectangle has the aspect of future_book's small cover, so a match cut can land on it."""
    from .bitmap import draw_text, draw_mark
    p = {**BOOK_DEFAULTS, **scene.p}; pal, E, A = scene.pal, scene.E, scene.A
    a = 1.0      # the book is fully present from frame 0 (no fade-in: first frames must be populated)
    W, H, cy, dy = p["book_w"], p["book_h"], p["book_y"], p["desk_y"]
    ink, cream = _hex("#060814"), _hex("#F4ECDC")
    if p["desk"]:
        cv.mask_fill(lambda x, y: y > dy, _hex("#7E1F35"), 1.0)
        cv.mask_fill(lambda x, y: (y > dy) & (y < dy + 3), _hex("#EC4A57"), .55)
        for k, yy in enumerate((dy + 14, dy + 31, dy + 52, dy + 70)):
            cv.line(-95, yy, 95, yy + (2 if k % 2 else -1), .8, _hex("#141E4A"), .45)
        cv.mask_fill(lambda x, y: (y > dy + 40) & (y < dy + 44), _hex("#141E4A"), .8)     # desk front edge
        # inkwell + quill (left)
        ix = -74.0
        cv.ellipse(ix, dy - 1, 10, 3, ink, .6)
        cv.rect(ix, dy - 7, 16, 12, _hex("#1E2E73"), 1.0); cv.rect(ix - 4, dy - 8, 3, 9, _hex("#4169D1"), 1.0)
        cv.rect(ix, dy - 14, 8, 3, _hex("#141E4A"), 1.0)
        cv.line(ix + 1, dy - 14, ix + 14, dy - 46, 1.2, cream, 1.0)
        cv.poly([(ix + 14, dy - 46), (ix + 20, dy - 52), (ix + 10, dy - 30), (ix + 7, dy - 26)], _hex("#B8CDF2"), 1.0)
    # candle (right) — warm light behind the book
    gx, gy = 76.0, dy
    if p["candle"]:
        fl = int(math.floor(lt * 10)) % 3                                     # 3-frame flame
        cv.glow(gx, gy - 34, 46, _hex("#FF9A86"), .35 + .06 * (fl == 1))
    # page block (thickness) + back cover
    cv.rect(4, cy + 4, W + 2, H, _hex("#141E4A"), a)
    cv.rect(3, cy + 2, W - 2, H - 3, _hex("#B8CDF2"), a)
    for k in range(0, int(H) - 8, 4):
        cv.line(W / 2 + 1, cy - H / 2 + 5 + k, W / 2 + 3, cy - H / 2 + 5 + k, .6, _hex("#77A2EE"), a)
    # right page under the cover (arrow, cracked)
    open_k = 1.0 - ease(min(1.0, max(0.0, lb / max(.05, p["close_at"]))), "inCubic") if p["state"] == "closing" else 0.0
    if open_k > 0:
        cv.rect(0, cy, W, H, cream, a); cv.matte(0, cy, W, H, .9)
        cv.rect(-W / 2 + 3, cy, 5, H, _hex("#B8CDF2"), a)
        ax, ay = 4, cy - 14
        for ddx, ddy in ((-4, 0), (4, 0), (0, -4), (0, 4)):
            draw_bitmap(cv, Bitmap(ARROW_L, ax + ddx, ay + ddy, 5.0), _hex("#0B4F5C"), a)
        draw_bitmap(cv, Bitmap(ARROW_L, ax, ay, 5.0), _hex("#41E8D2"), a)
        for seg in [[(-1, -6), (1, -2), (-1, 1), (2, 4), (0, 7)], [(1, -2), (5, -1), (8, -3)], [(-1, 1), (-5, 2), (-7, 0)]]:
            pts = [(ax + 5 * u, ay + 5 * v) for u, v in seg]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]): cv.line(x0, y0, x1, y1, 3.2, _hex("#EC4A57"), a)
        from .sprites import ROLES
        L = {}
        for r, row in enumerate(MINI_HERO):
            for c, ch in enumerate(row):
                if ch != ".": L.setdefault(ch, np.zeros((7, 7), bool))[r, c] = True
        for ch, m in L.items(): draw_bitmap(cv, Bitmap(m, 4, cy + 42, 4.0), _hex(ROLES[ch]), a)
    # the cover: closed rect, or a quad swinging around the spine (left edge)
    cw = W * math.cos(open_k * math.pi)
    x0 = -W / 2
    lift = 10 * math.sin(open_k * math.pi)
    if abs(cw) > 1:
        quad = [(x0, cy - H / 2), (x0 + cw, cy - H / 2 - lift), (x0 + cw, cy + H / 2 + lift), (x0, cy + H / 2)]
        cv.poly(quad, _hex("#2C47A6") if cw > 0 else _hex("#1E2E73"), a)
        cv.poly_outline(quad, ink, a)
    if open_k == 0:
        cv.matte(0, cy, W, H, .8)
        cv.rect(0, cy, W - 8, H - 8, _hex("#F4ECDC"), a * .9)                    # embossed cream frame
        cv.rect(0, cy, W - 12, H - 12, _hex("#2C47A6"), a)
        cv.line(x0 + 3, cy - H / 2 + 2, x0 + 3, cy + H / 2 - 2, 2, _hex("#77A2EE"), a)   # spine highlight
        for sx in (-1, 1):
            for sy in (-1, 1): cv.disc(sx * (W / 2 - 10), cy + sy * (H / 2 - 10), 2.2, _hex("#FF9A86"), a)
        draw_mark(cv, pal, 0, cy - 46, 2.0, alpha=a, glow=0, outline=ink, snap=True)
        draw_text(cv, p["title"], 0, cy - 8, 2, cream, a, snap=True)
        cv.line(-30, cy + 16, 30, cy + 16, 1.2, _hex("#FF9A86"), a)
        if scene.p.get("brand") and lb >= p.get("brand_at", 1.0):
            kb = ease(min(1.0, (lb - p.get("brand_at", 1.0)) / .5), "outCubic")
            cv.rect(0, cy + 47, 98, 44, ink, a * kb)
            cv.rect(0, cy + 47, 96, 42, _hex("#141E4A"), a * kb)
            cv.rect(0, cy + 47, 92, 38, ink, a * kb)
            cv.matte(0, cy + 47, 98, 44, 1.0)
            h = scene.p["brand"]; two = h.split(".", 1)
            l1, l2 = (two[0], "." + two[1]) if len(two) == 2 else (h, "")
            draw_text(cv, l1, 0, cy + 38, 2, _hex("#41E8D2"), a * kb, snap=True)
            if l2: draw_text(cv, l2, 0, cy + 57, 2, _hex("#41E8D2"), a * kb, snap=True)
            if kb < 1: cv.glow(0, cy + 47, 50, E(.8), .3 * (1 - kb))
    if p["candle"]:
        fl = int(math.floor(lt * 10)) % 3
        cv.rect(gx, gy - 12, 11, 24, cream, 1.0); cv.rect(gx + 3.5, gy - 12, 3, 24, _hex("#B8CDF2"), 1.0)
        cv.ellipse(gx, gy - 24, 5.5, 1.6, _hex("#FFFFFF"), 1.0)
        cv.line(gx, gy - 24, gx, gy - 27, .8, ink, 1.0)
        fh, fw = ((9, 3.2), (11, 2.8), (8, 3.6))[fl]; sway = (0, .8, -.6)[fl]
        cv.ellipse(gx + sway * .5, gy - 27 - fh / 2, fw, fh / 2, _hex("#EC4A57"), 1.0)
        cv.ellipse(gx + sway, gy - 27 - fh * .45, fw * .55, fh * .3, _hex("#FF9A86"), 1.0)
        cv.disc(gx + sway, gy - 28.5, 1.1, cream, 1.0)
        cv.glow(gx, gy - 31, 18, _hex("#FF9A86"), .55)
        for i in range(int(p["dust"])):                                       # dust motes drifting in the light
            r = np.random.default_rng(300 + i)
            ph = float(r.uniform(0, 1)); sp = float(r.uniform(.04, .09))
            u = (ph + lt * sp) % 1.0
            mx = gx - 40 + float(r.uniform(-30, 30)) + 6 * math.sin(lt * .9 + i)
            my = gy - 10 - u * 120
            cv.disc(mx, my, .7, _hex("#FFD9C7") if i % 3 else cream, .7 * math.sin(math.pi * u))



from .scenes import SCENES  # noqa: E402
SCENES.update({"future_book": FutureBook, "laplace_demon": LaplaceDemon, "dominoes": Dominoes, "libet_clock": LibetClock, "future_tree": FutureTree})
