"""Vision scenes: one living world rendered as a G-buffer (albedo + uv / temp / depth / oid) for the vision pass.

vision_world   coastal meadow (canli-gozu layout, world origin = frame centre, art units): sky + clouds + sun/moon,
               hills, tree with a hanging bat, beehive with bees, the bullseye flower, a bee on a flight track, a
               butterfly, wind-blown grass, red ball, stone, mouse, shore + sea with shimmer, seabed, mantis shrimp.
               All motion is a function of the GLOBAL beat with an integer number of cycles per film, so consecutive
               segments (eye switches) continue the same world and the loop seam is exact.
vision_mosaic  2×3 tiles of the same world through six modes (final image, each tile in its own palette).

params (vision_world): time day|dusk|night, focus flower|ball|mouse|bat|shrimp|hive|bat_hive, uv_glow, dog (S3 snout),
snake (S4 head), underwater (caustics + bubbles), bat_close (bat ×1.25), bee_keys [[beat, x, y], ...] (optional
override of the default bee flight track; beats are global, negative = before the loop seam)."""
import math
import numpy as np
from .scenes import Scene, SCENES, ease

TAU = math.pi * 2
ANCHORS = {"flower": (2.0, 22.0), "ball": (-48.0, 76.0), "mouse": (60.0, 78.0), "bat": (-46.0, -52.0),
           "shrimp": (2.0, 128.0), "hive": (50.0, 8.0), "hive_label": (50.0, 6.0), "bat_hive": (2.0, -22.0), "bee": (22.0, 2.0)}
# default bee track (global beats; the loop wraps beats ≥ total-6 to negative): leaves the hive, hovers toward the
# flower (S1 hook frame 0 = (22, 2)), lands (S2), stays, takes off for the mosaic, goes home before night
BEE_KEYS = [(-6, 50, 24), (-4.6, 50, 24), (-3, 43, 14), (-1.5, 31, 6), (0, 22, 2), (3, 17, -2), (6, 20, 3), (8, 15, 6),
            (10, 11, 11), (12, 9, 14.5), (60, 9, 14.5), (62, 15, 5), (65, 25, -1), (68, 17, 1), (71, 27, 4), (74, 38, 12),
            (76.8, 50, 24), (200, 50, 24)]
PERCH = (12.0, 60.0)
HIVE = (50.0, 8.0)


def _h(i, j, s=0.0):
    v = np.sin(np.asarray(i, np.float64) * 127.1 + np.asarray(j, np.float64) * 311.7 + s * 74.7) * 43758.5453
    return (v - np.floor(v)).astype(np.float32)


def vnoise(x, y, s=0.0):
    """smooth value noise (0..1), any scale; world-anchored so it never swims with the camera."""
    xi, yi = np.floor(x), np.floor(y); fx, fy = x - xi, y - yi
    ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _h(xi, yi, s), _h(xi + 1, yi, s); c, d = _h(xi, yi + 1, s), _h(xi + 1, yi + 1, s)
    return (a + (b - a) * ux) * (1 - uy) + (c + (d - c) * ux) * uy


def _catmull(keys, B):
    ts = [k[0] for k in keys]
    j = max(0, min(len(keys) - 2, int(np.searchsorted(ts, B, "right")) - 1))
    p0, p1, p2, p3 = keys[max(j - 1, 0)], keys[j], keys[j + 1], keys[min(j + 2, len(keys) - 1)]
    u = min(max((B - p1[0]) / max(p2[0] - p1[0], 1e-6), 0.0), 1.0)
    out = []
    for c in (1, 2):
        a, b, cc, d = p0[c], p1[c], p2[c], p3[c]
        out.append(.5 * ((2 * b) + (-a + cc) * u + (2 * a - 5 * b + 4 * cc - d) * u * u + (-a + 3 * b - 3 * cc + d) * u ** 3))
    return out


LIGHT = {"day": (1.0, 1.0, 1.0), "dusk": (.86, .64, .56), "night": (.46, .54, .86)}
SKY = {"day": ((.30, .55, .92), (.72, .87, 1.0)), "dusk": ((.22, .18, .42), (1.0, .58, .38)),
       "night": ((.02, .03, .10), (.16, .22, .46))}
SKY_ALPHA = {"day": .82, "dusk": .8, "night": .5}


class VisionWorld(Scene):
    writes_aux = True
    defaults = {"time": "day", "focus": "flower", "uv_glow": False, "dog": False, "snake": False, "underwater": False,
                "bat_close": False, "bee_keys": None}

    def attach(self, film): self.film = film
    film = None

    # ---------- global clock
    def B(self, lb):
        return self.b0 + lb

    def cyc(self, B, period):
        """phase (radians) of a motion with `period` beats, snapped to an integer number of cycles per film."""
        if self.total > 0:
            n = max(1, round(self.total / period)); return TAU * n * B / self.total
        return TAU * B / period

    def bee_state(self, B):
        if self.loop and self.total and B >= self.total - 6: B -= self.total
        keys = [tuple(k) for k in (self.p.get("bee_keys") or BEE_KEYS)]
        x, y = _catmull(keys, B)
        perch = min(1.0, max(0.0, min(B - PERCH[0], PERCH[1] - B) / 1.2)) if PERCH[0] < B < PERCH[1] else 0.0
        a = 1.4 * (1 - perch)
        x += a * math.sin(self.cyc(B, 2 / 3)); y += a * .6 * math.sin(self.cyc(B, 1 / 3))
        vis = -4.6 < B < 76.8
        x2, _ = _catmull(keys, B + .1)
        return x, y, vis, perch, (1 if x2 >= x else -1)

    def anchor(self, name, lb):
        if name == "bee":
            x, y, *_ = self.bee_state(self.B(lb)); return (x, y)
        return ANCHORS.get(name, ANCHORS["flower"])

    def focus(self, lb, dur_b):
        return self.anchor(self.p.get("focus", "flower"), lb)

    # ---------- drawing
    def draw(self, cv, lt, lb, dur_b):
        B = self.B(lb); wx, wy = cv.world_grid(); H, W = wy.shape
        tod = self.p.get("time", "day"); night = tod == "night"
        self.alb = np.zeros((H, W, 3), np.float32); self.cover = np.zeros((H, W), bool)
        self.uv = np.zeros((H, W), np.float32); self.temp = np.zeros((H, W), np.float32)
        self.depth = np.ones((H, W), np.float32); self.oid = np.zeros((H, W), np.int32)
        self.emit = np.zeros((H, W), bool)
        self.wx, self.wy, self._B = wx, wy, B
        self._sky(cv, B, tod)
        self._hills(tod)
        self._meadow(B)
        self._tree(B)
        self._bat(B, lb)
        self._hive(B, tod)
        self._sea(B)
        self._shrimp(B)
        self._flower(B)
        self._ball(); self._stone(); self._mouse(B)
        if tod != "night": self._butterfly(B)
        self._bee(B)
        if self.p.get("dog"): self._dog(lb)
        if self.p.get("snake"): self._snake(lb, B)
        if night: self._fireflies(cv, B)
        # lighting (albedo only; emissive sun/moon/fireflies unlit), then composite over the back layers
        L = np.asarray(LIGHT.get(tod, LIGHT["day"]), np.float32)
        lit = np.where(self.emit[..., None], self.alb, self.alb * L)
        a = np.where(self.cover, 1.0, SKY_ALPHA.get(tod, .8)).astype(np.float32)[..., None]
        cv.rgb[:] = cv.rgb * (1 - a) + lit * a
        aux = cv.aux
        if aux is not None:
            aux["uv"][:] = self.uv; aux["temp"][:] = self.temp; aux["depth"][:] = self.depth; aux["oid"][:] = self.oid
        if tod == "day": cv.glow(56, -122, 16, (1.0, .95, .75), .35)
        if night and getattr(self, "_lantern", None):
            lx, ly, fl = self._lantern; cv.glow(lx, ly, 20, (1.0, .78, .40), .45 * fl); self._lantern = None

    def put(self, m, col, uv, temp, depth, oid):
        if not m.any(): return
        c = np.asarray(col, np.float32)
        self.alb[m] = c if c.ndim == 1 else c[m]
        for buf, v in ((self.uv, uv), (self.temp, temp), (self.depth, depth)):
            buf[m] = v if np.isscalar(v) else np.asarray(v)[m]
        self.oid[m] = oid; self.cover[m] = True

    def _ell(self, cx, cy, rx, ry):
        return ((self.wx - cx) / rx) ** 2 + ((self.wy - cy) / ry) ** 2 <= 1

    # sky, clouds, sun / moon
    def _sky(self, cv, B, tod):
        wx, wy = self.wx, self.wy
        g = np.clip((wy + 160) / 150, 0, 1)[..., None]
        top, hor = (np.asarray(c, np.float32) for c in SKY.get(tod, SKY["day"]))
        sky = top * (1 - g) + hor * g
        self.alb[:] = sky; self.uv[:] = .75; self.temp[:] = .04; self.depth[:] = 1.0
        sx, sy = 56.0, -122.0; r = np.hypot(wx - sx, wy - sy)
        if tod == "night":
            moon = r < 8
            crater = moon & (vnoise(wx * .5, wy * .5, 3) > .62)
            self.alb[moon] = (.92, .93, .86); self.alb[crater] = (.70, .72, .70); self.emit |= moon
            self.uv[moon] = .6; self.temp[moon] = .06
        else:
            sun = r < 11
            col = (1.0, .97, .80) if tod == "day" else (1.0, .70, .42)
            self.alb[sun] = col; self.emit |= sun; self.uv[sun] = 1.0; self.temp[sun] = .25
            halo = (r >= 11) & (r < 15)
            self.alb[halo] = self.alb[halo] * .6 + np.asarray(col, np.float32) * .4
        # clouds drift right, wrap on a 320-unit span (integer wraps per film)
        span = 330.0
        for k, (x0, y0, s) in enumerate(((-40, -132, 1.0), (60, -104, .8), (150, -142, 1.2), (230, -96, .7))):
            ph = (B / self.total if self.total else B / 88.0) + k * .0
            cx = ((x0 + span * ph * 1.0 + 165) % span) - 165
            m = np.zeros_like(wx, bool)
            for dx, dy, rr in ((0, 0, 9), (-9, 2.5, 6.5), (9, 2, 7), (-16, 5, 4.5), (16, 4.5, 5), (4, -5, 6.5)):
                m |= np.hypot((wx - cx - dx * s) / 1.25, wy - y0 - dy * s) < rr * s
            m &= wy < y0 + 7 * s
            shade = np.clip((wy - (y0 - 8 * s)) / (16 * s), 0, 1)[..., None]
            base = {"day": ((1.0, 1.0, 1.0), (.78, .84, .94)), "dusk": ((1.0, .78, .66), (.62, .42, .55)),
                    "night": ((.22, .26, .40), (.12, .14, .26))}[tod]
            c = np.asarray(base[0], np.float32) * (1 - shade) + np.asarray(base[1], np.float32) * shade
            self.alb[m] = c[m]; self.uv[m] = .8; self.temp[m] = .05
            if tod == "night": self.emit[m] = True

    def _hills(self, tod):
        wx, wy = self.wx, self.wy
        far = (wy > -40 + 7 * np.sin(wx / 31 + 2.1) + 4 * np.sin(wx / 13)) & (wy < -8)
        self.put(far, (.44, .60, .62) if tod != "dusk" else (.52, .44, .56), .2, .22, .92, 2)
        h = -32 + 10 * np.sin((wx + 90) / 23 + 1) + 6 * np.sin((wx + 90) / 9)
        hill = (wy > h) & (wy < -6)
        sh = np.clip((wy - h) / 18, 0, 1)[..., None]
        col = np.asarray((.30, .52, .34), np.float32) * (1 - sh * .3) + vnoise(wx * .15, wy * .3, 5)[..., None] * .05
        self.put(hill, col, .12, .25, .85, 2)
        # a few far trees on the ridge
        for tx in (-18, 14, 84, 104):
            ty = -32 + 10 * math.sin((tx + 90) / 23 + 1) + 6 * math.sin((tx + 90) / 9)
            m = self._ell(tx, ty - 3, 3.2, 4.5)
            self.put(m, (.20, .40, .26), .1, .27, .84, 2)

    def _meadow(self, B):
        wx, wy = self.wx, self.wy
        mead = wy >= -10
        gd = np.clip(1 - (wy + 10) / 110, .05, 1)
        n1 = vnoise(wx * .06, wy * .12, 1); n2 = vnoise(wx * .3, wy * .55, 2)
        far = np.asarray((.40, .62, .36), np.float32); near = np.asarray((.18, .46, .14), np.float32)
        col = far * gd[..., None] + near * (1 - gd[..., None])
        col = col * (.86 + .26 * n1[..., None]) + (n2[..., None] - .5) * np.asarray((.05, .07, .03), np.float32)
        self.put(mead, col, .08, .32 + .04 * n2, gd * .6, 3)
        # wind-blown grass blades in depth bands (taller toward the camera); wind = travelling gust, 4-beat period
        ph = self.cyc(B, 4.0)
        for k, yb in enumerate(np.arange(-6.0, 104.0, 6.5)):
            Hm = 2.2 + (yb + 10) * .075; sp = 1.3 + (yb + 10) * .012
            j0 = np.floor(wx / sp + k * .37)
            ybj = yb + 3.2 * (_h(j0, k, 5) - .5)                       # per-blade baseline jitter (no visible rows)
            rel = (ybj - wy) / Hm
            band = (rel > 0) & (rel < 1) & mead
            if not band.any(): continue
            lean = (1.2 + .02 * (yb + 10)) * (np.sin(ph - wx * .045 + k * .3) * .75 + .25 * np.sin(2 * ph - wx * .11)) * rel ** 2
            u = (wx - lean) / sp + k * .37
            j = np.floor(u); f = u - j
            hb = .45 + .55 * _h(j, k, 7)
            thick = .62 * (1 - rel / hb)
            blade = band & (rel < hb) & (f < thick)
            tip = rel / hb
            tw = np.clip(tip * 1.3 - .3, 0, 1)[..., None]              # base melts into the ground colour
            c = col * (1 - tw) + np.asarray((.66, .84, .32), np.float32) * tw
            c = c * (.85 + .3 * _h(j, k, 9))[..., None]
            d = np.clip(1 - (yb + 10) / 110, .05, 1) * .6
            self.put(blade, c, .08, .33, d, 3)
            # wildflowers on some tips (white / violet with UV / yellow)
            fl = band & (_h(j, k, 11) > .93) & (np.abs(rel - hb) < .14 + .02 * Hm / 4) & (np.abs(f - .25) < .5)
            if fl.any():
                kind = _h(j, k, 13)
                fc = np.where((kind < .4)[..., None], np.asarray((.96, .94, .90), np.float32),
                              np.where((kind < .7)[..., None], np.asarray((.62, .42, .90), np.float32), np.asarray((1.0, .86, .25), np.float32)))
                self.put(fl, fc, np.where(kind < .4, .2, np.where(kind < .7, .8, .1)), .34, d, 21)

    def _tree(self, B):
        wx, wy = self.wx, self.wy
        trunk = (np.abs(wx + 75 + .8 * np.sin(wy / 9)) < 6 - np.clip((wy + 90) / 140, 0, 1) * -1.5) & (wy > -96) & (wy < 56)
        bark = vnoise(wx * .9, wy * .12, 4)
        tc = np.asarray((.34, .22, .13), np.float32) * (.75 + .4 * bark[..., None])
        self.put(trunk, tc, .05, .36, .30, 4)
        roots = (wy > 50) & (wy < 58) & (np.abs(wx + 75) < 9 - (58 - wy) * .4)
        self.put(roots, (.30, .20, .12), .05, .35, .30, 4)
        br = (wx > -73) & (wx < -36) & (np.abs(wy - (-62 - (wx + 72) * .15)) < 2.0 - (wx + 72) * .025)
        self.put(br, (.36, .24, .14), .05, .36, .30, 4)
        sw = .9 * math.sin(self.cyc(B, 2.0))
        n = vnoise((wx - sw) * .22, wy * .22, 6); n2 = vnoise((wx - sw) * .6, wy * .6, 8)
        can = np.zeros_like(wx, bool)
        for cx, cy, rx, ry in ((-66, -96, 39, 27), (-40, -86, 18, 18), (-90, -84, 20, 18), (-58, -122, 22, 14), (-80, -112, 18, 14)):
            can |= ((wx - cx - sw) / rx) ** 2 + ((wy - cy) / ry) ** 2 <= (.82 + .3 * n) ** 2
        light = np.clip(.5 - (wy + 96) / 70 - (wx + 66) / 120, 0, 1)
        cc = np.asarray((.10, .30, .12), np.float32) + light[..., None] * np.asarray((.14, .24, .06), np.float32)
        cc = cc * (.8 + .4 * n2[..., None])
        self.put(can, cc, .1, .3, .32, 5)
        hi = can & (n2 > .78) & (light > .15)
        self.put(hi, (.46, .70, .26), .12, .3, .32, 5)

    def _bat(self, B, lb):
        s = 1.6 if self.p.get("bat_close") else 1.0
        bx, by = ANCHORS["bat"]; wx, wy = self.wx, self.wy
        br = 1 + .05 * math.sin(self.cyc(B, 2.0))
        tw = 0.0
        if self.film is not None and self.p.get("sonar"):
            hits = [h for h in self.film.drum_hits("B") if h <= B]
            if hits: tw = math.exp(-(B - hits[-1]) * 9)
        dx, dy = (wx - bx) / s, (wy - by) / s
        feet = (np.abs(dx) < 1.9) & (np.abs(np.abs(dx) - 1.2) < .55) & (dy > -9.5) & (dy < -5)
        body = (dx / 3.4) ** 2 + (dy / (5.5 * br)) ** 2 <= 1
        span = 4.6 + 5.5 * tw
        wing = (np.abs(dx) < span) & (dy > -6) & (dy < 3.5) & ((np.abs(dx) / span) ** 2 + ((dy + 1) / 4.6) ** 2 <= 1)
        head = ((dx / 2.8) ** 2 + ((dy - 6) / 2.4) ** 2 <= 1)
        ears = (dy > 7) & (dy < 10.5) & (np.abs(np.abs(dx) - 1.6) < (10.5 - dy) * .28)
        self.put(feet, (.16, .12, .10), .04, .7, .28, 6)
        self.put(wing, (.13, .09, .09), .04, .85, .28, 6)
        self.put(body, (.26, .18, .14), .04, .92, .28, 6)
        self.put(head | ears, (.24, .17, .13), .04, .92, .28, 6)
        # S9: head turns to camera at local beat 6 — eyes catch the light (turquoise glint = the eye mark)
        k = ease((lb - 6.0) / .6, "outCubic") if self.p.get("bat_close") else 0.0
        if k > 0:
            for ex in (-1.1, 1.1):
                e = ((dx - ex) / .75) ** 2 + ((dy - 6.3) / .75) ** 2 <= k
                self.put(e, (.70, 1.0, .95), .2, .9, .27, 6); self.emit |= e

    def _hive(self, B, tod):
        """Three-box wooden hive on a stand (body x 26..74, y -20..25), roof, entrance slit; bees in/out by day,
        a small lantern on a post at night (light source for the brand-night label)."""
        wx, wy = self.wx, self.wy; hx, hy = HIVE
        legs = (np.abs(np.abs(wx - hx) - 19) < 1.5) & (wy > 24) & (wy < 34)
        self.put(legs, (.30, .20, .12), .1, .4, .23, 7)
        box = (np.abs(wx - hx) < 24) & (wy > -20) & (wy < 25)
        grain = vnoise(wx * .25, wy * 2.2, 12)
        wood = np.asarray((.82, .60, .34), np.float32) * (.86 + .22 * grain[..., None])
        self.put(box, wood, .3, .62, .22, 7)
        seam = box & ((np.abs(wy + 5) < .6) | (np.abs(wy - 10) < .6))
        self.put(seam, (.50, .34, .19), .25, .6, .22, 7)
        hand = box & (np.abs(wx - hx) < 6) & ((np.abs(wy + 12.5) < .9) | (np.abs(wy - 17.5) < .0))
        self.put(hand, (.45, .30, .17), .25, .6, .22, 7)
        side = box & (wx > hx + 19)
        self.alb[side] *= .8
        roof = (np.abs(wx - hx) < 27) & (wy > -26) & (wy <= -20)
        self.put(roof, (.48, .33, .20), .25, .55, .22, 7)
        roofl = (np.abs(wx - hx) < 27) & (wy > -26) & (wy < -24.4)
        self.put(roofl, (.66, .46, .28), .25, .55, .22, 7)
        ent = (np.abs(wx - hx) < 8) & (wy > 21) & (wy < 24)
        self.put(ent, (.10, .07, .05), 0.0, .78, .22, 7)
        if tod != "night":
            for k in range(3):
                a = self.cyc(B, 2.0 + k * .5) + k * 2.1
                x = hx + (8 + 3 * k) * math.cos(a); y = 22 + (3 + k) * math.sin(a * 2) - 2 * k
                m = self._ell(x, y, 1.3, 1.0)
                self.put(m, (.95, .78, .15), .15, .55, .2, 12)
        else:
            post = (np.abs(wx - (hx + 31)) < .9) & (wy > -22) & (wy < 32)
            arm = (wx > hx + 26) & (wx < hx + 31) & (np.abs(wy + 22) < .7)
            self.put(post | arm, (.22, .16, .12), .05, .3, .21, 28)
            lamp = self._ell(hx + 26.5, -17.5, 1.9, 2.6)
            fl = .85 + .15 * math.sin(self.cyc(B, .5))
            self.put(lamp, (1.0, .86 * fl, .45), .2, .7, .2, 28); self.emit |= lamp
            self._lantern = (hx + 26.5, -17.5, fl)

    def _sea(self, B):
        wx, wy = self.wx, self.wy; ph = self.cyc(B, 4.0)
        shore = 102 + 1.6 * np.sin(wx / 14 + ph) + .8 * np.sin(wx / 5 - 2 * ph)
        sea = wy >= shore
        dpt = np.clip((wy - 102) / 110, 0, 1)
        col = np.asarray((.10, .45, .58), np.float32) * (1 - dpt[..., None]) + np.asarray((.03, .14, .28), np.float32) * dpt[..., None]
        sh = 1 + .18 * np.sin(wx / 5 + wy / 3 + self.cyc(B, 2.0)) * (1 - dpt)
        col = col * sh[..., None]
        uw = self.p.get("underwater")
        caust = np.abs(np.sin(wx * .21 + np.sin(wy * .13 + ph) * 2) + np.sin(wy * .27 - wx * .07 + ph * 2)) < (.32 if uw else .2)
        col = np.where((caust & (dpt < .6))[..., None], col * 1.35 + .06, col)
        self.put(sea, col, .3, .18, .18 - .04 * dpt, 16)
        foam = sea & (wy < shore + 2.2 + .8 * np.sin(wx / 3 + ph * 3))
        self.put(foam, (.86, .94, .96), .5, .2, .17, 16)
        glint = sea & (dpt < .25) & (_h(np.floor(wx / 2), np.floor(wy / 2), np.floor((B % self.total if self.total else B) * 2 + 1e-6) % 997) > .985)
        self.put(glint, (.95, .99, 1.0), .6, .2, .17, 16)
        btop = 152 + 4 * np.sin(wx / 20) + 2 * np.sin(wx / 7)
        bed = sea & (wy > btop)
        bd = np.clip((wy - btop) / 60, 0, 1)
        rip = np.sin(wx * .45 + wy * .9 + 2 * np.sin(wx * .07)) > .55
        sand = np.asarray((.58, .52, .38), np.float32) * (.82 + .26 * vnoise(wx * .4, wy * .4, 14)[..., None])
        sand = sand * np.where(rip, 1.12, .92)[..., None] * (1 - .45 * bd[..., None])
        self.put(bed, sand, .25, .17, .16, 19)
        peb = bed & (_h(np.floor(wx / 3), np.floor(wy / 3), 21) > .96) & (np.hypot((wx % 3) - 1.5, (wy % 3) - 1.5) < 1.1)
        pc = np.asarray((.42, .40, .40), np.float32) + _h(np.floor(wx / 3), np.floor(wy / 3), 22)[..., None] * .25
        self.put(peb, pc, .2, .17, .155, 19)
        for k, (sx, sy) in enumerate(((-12, 162), (28, 166), (-48, 174), (60, 170))):
            r = np.hypot(wx - sx, wy - sy); a = np.arctan2(wy - sy, wx - sx)
            shell = bed & (r < 3.2) & (a < 0.3) & (a > -np.pi - .3)
            self.put(shell, (.95, .82, .76), .55, .17, .15, 26)
            self.put(shell & (np.abs(np.sin(a * 4)) < .25), (.80, .55, .50), .5, .17, .15, 26)
        # small fish crossing the water column (periodic: integer laps per film)
        for k, (fy, per, sz, col) in enumerate(((112, 22.0, 1.0, (.98, .62, .20)), (118, 29.33, .8, (.90, .90, .40)), (124, 17.6, .7, (.40, .80, .95)))):
            u = ((B / per + k * .37) % 1.0); fx = -110 + 220 * u if k % 2 == 0 else 110 - 220 * u
            dirx = 1 if k % 2 == 0 else -1
            fyy = fy + 2 * math.sin(self.cyc(B, 2.0) + k)
            dx, dy = (wx - fx) * dirx, wy - fyy
            fbody = ((dx / (3.4 * sz)) ** 2 + (dy / (1.7 * sz)) ** 2 <= 1)
            ftail = (dx < -2.6 * sz) & (dx > -5.4 * sz) & (np.abs(dy) < (-dx - 2.6 * sz) * .8)
            self.put((fbody | ftail) & sea, col, .5, .19, .17, 27 + k)
        for cx, cy, rx, ry in ((-70, 146, 16.8, 9.8), (70, 142, 14.4, 8.4), (-30, 160, 12, 7), (95, 126, 10, 6), (2, 141, 30, 7.5)):
            m = self._ell(cx, cy, rx, ry) & sea
            rc = np.asarray((.40, .36, .32), np.float32) * (.8 + .3 * vnoise(wx * .5, wy * .5, 15)[..., None])
            self.put(m, rc, .15, .2, .15, 17)
        for k, sx in enumerate((-52, -40, 38, 50, 82)):
            base = 150 + 4 * math.sin(sx / 20)
            rel = (base - wy) / 22
            sway = 3 * np.sin(self.cyc(B, 3.0) + k + rel * 2) * rel
            weed = sea & (rel > 0) & (rel < 1) & (np.abs(wx - sx - sway) < 1.4 * (1 - rel * .6))
            self.put(weed, (.16, .52, .26), .2, .18, .15, 22)
        if uw:
            for k in range(6):
                bxp = -10 + k * 9 + 3 * math.sin(k * 1.7)
                u = ((B / 4.0 + k / 6) % 1.0)
                byp = 132 - u * 34
                m = (np.abs(np.hypot(wx - bxp - math.sin(u * 9 + k), wy - byp) - 1.4) < .55) & (wy > shore + 2)
                self.put(m, (.70, .90, .96), .45, .18, .17, 16)

    def _shrimp(self, B):
        wx, wy = self.wx, self.wy
        ph = self.cyc(B, 2.0)
        yc = 128 + 3 * np.sin((wx + 18) / 6 - ph * .5)
        th = 3.8 - np.clip((-wx + 4) / 22, 0, 1) * 1.6
        body = (np.abs(wy - yc) < th) & (wx > -18) & (wx < 22)
        si = np.clip(((wx + 18) // 6.7).astype(int), 0, 5)
        cols = np.array([[.10, .75, .35], [.15, .55, .90], [.95, .30, .20], [.95, .75, .15], [.60, .20, .80], [.10, .85, .70]], np.float32)
        band = np.abs(((wx + 18) % 6.7) - 6.6) < .7
        c = cols[si] * np.where(band, .6, 1.0)[..., None]
        uvv = .5 + .4 * (si % 2)
        tail = (wx <= -18) & (wx > -26) & (np.abs(wy - (128 + 3 * math.sin(-ph * .5))) < (wx + 27) * .55)
        legs = (wy > yc + th - .5) & (wy < yc + th + 3) & (np.abs(((wx + 18) % 4) - 2) < .5) & (wx > -14) & (wx < 18)
        self.put(tail, (.20, .80, .60), .7, .2, .14, 18)
        self.put(legs, (.95, .45, .30), .5, .2, .14, 18)
        self.put(body, c, uvv, .2, .14, 18)
        # stalked eyes scanning (Thoen: scanning eye movements)
        a = -1.2 + .45 * math.sin(self.cyc(B, 2.0) * 1.0)
        for k, off in enumerate((0.0, .5)):
            ex, ey = 22 + 4 * math.cos(a + off), 126 + 4 * math.sin(a + off)
            st = (np.abs((wx - 21) * math.sin(a + off) - (wy - 126) * math.cos(a + off)) < .55) & (np.hypot(wx - 21, wy - 126) < 4)
            self.put(st, (.85, .40, .45), .6, .2, .14, 18)
            self.put(np.hypot(wx - ex, wy - ey) < 1.6 + .6 * (k == 0), (.95, .30, .50), .9, .2, .14, 18)
        ant = (np.abs(wy - (124 - (wx - 22) * .55 + 1.2 * np.sin(ph + wx * .3))) < .45) & (wx > 22) & (wx < 34)
        self.put(ant, (.95, .70, .40), .5, .2, .14, 18)

    def _flower(self, B):
        wx, wy = self.wx, self.wy
        sw = 1.0 * math.sin(self.cyc(B, 4.0) + .5)
        FX, FY = 2.0 + sw, 22.0
        rel = np.clip((92 - wy) / 70, 0, 1)
        stem = (np.abs(wx - (2 + sw * rel)) < 1.6) & (wy > FY) & (wy < 92)
        self.put(stem, (.18, .55, .20), .06, .34, .12, 9)
        for sgn, ly in ((-1, 60), (1, 72)):
            lx = 2 + sw * (92 - ly) / 70
            m = (((wx - lx - sgn * 6) / 6.5) ** 2 + ((wy - ly + (wx - lx) * sgn * .35) / 2.2) ** 2 <= 1)
            self.put(m, (.20, .58, .22), .06, .34, .12, 9)
        r = np.hypot(wx - FX, wy - FY); a = np.arctan2(wy - FY, wx - FX)
        pet = (r < 9 + 15 * np.abs(np.cos(4 * a)) ** .6) & (r > 4)
        k = np.clip((r - 4) / 20, 0, 1)[..., None]
        pc = np.asarray((.98, .70, .06), np.float32) * (1 - k) + np.asarray((1.0, .90, .18), np.float32) * k
        vein = np.abs(np.cos(4 * a)) > .985
        pc = np.where((vein & (r > 6))[..., None], pc * .88, pc)
        tips = .92
        if self.p.get("uv_glow"): tips = .9 + .1 * (.5 + .5 * math.sin(self.cyc(B, 1.0)))
        self.put(pet, pc, np.where(r > 13, tips, 0.0), .40, .11, 10)
        disc = r <= 5.5
        dc = np.asarray((.45, .25, .08), np.float32) * (.8 + .4 * vnoise(wx * 1.2, wy * 1.2, 16)[..., None])
        self.put(disc, dc, 0.0, .42, .10, 11)

    def _ball(self):
        wx, wy = self.wx, self.wy
        sh = self._ell(-46, 86.5, 11, 2.6)
        self.alb[sh] *= .6
        m = np.hypot(wx + 48, wy - 76) < 10
        d = np.hypot(wx + 52, wy - 72) / 10
        shade = np.clip(1.12 - .38 * d, .72, 1.12)[..., None]
        c = np.asarray((.92, .12, .12), np.float32) * shade
        self.put(m, c, .04, .33, .08, 13)
        spec = np.hypot(wx + 52, wy - 71.5) < 1.8
        self.put(spec & m, (1.0, .80, .76), .1, .33, .08, 13)

    def _stone(self):
        wx, wy = self.wx, self.wy
        m = self._ell(36, 86, 11.7, 7.2)
        sh = np.clip(.75 + .35 * (-(wy - 86) / 7.2 - (wx - 36) / 23), .55, 1.15)
        c = np.asarray((.55, .55, .55), np.float32) * sh[..., None] * (.9 + .2 * vnoise(wx * .6, wy * .6, 17)[..., None])
        self.put(m, c, .25, .14, .09, 14)

    def _mouse(self, B):
        wx, wy = self.wx, self.wy
        sn = .5 * math.sin(self.cyc(B, .25))
        fl = math.sin(self.cyc(B, 2.0))
        t = np.clip((46 - wx) / -8, 0, 1)
        tail = (wx > 44) & (wx < 54) & (np.abs(wy - (83 - (wx - 44) * .2 - 2.2 * fl * (1 - (wx - 44) / 10) ** 2)) < .7)
        self.put(tail, (.62, .46, .46), .08, .9, .08, 15)
        body = self._ell(60, 80, 7.7, 5.0)
        c = np.asarray((.50, .44, .40), np.float32) * np.clip(1.1 - (wy - 76) / 14, .7, 1.1)[..., None]
        self.put(body, c, .08, 1.0, .08, 15)
        head = self._ell(67.5 + sn * .3, 76.5, 3.6, 3.0)
        self.put(head, (.52, .46, .42), .08, 1.0, .08, 15)
        ear = self._ell(65.5, 72.8, 1.8, 1.8)
        self.put(ear, (.80, .55, .55), .08, .95, .08, 15)
        nose = self._ell(71.2 + sn, 77.2, .9, .8)
        self.put(nose, (.85, .50, .52), .08, .98, .08, 15)
        eye = self._ell(68.6, 75.6, .6, .6)
        self.put(eye, (.05, .04, .04), .05, 1.0, .08, 15)

    def _butterfly(self, B):
        wx, wy = self.wx, self.wy
        x = -18 + 30 * math.sin(self.cyc(B, 22.0)); y = 34 + 16 * math.sin(self.cyc(B, 88 / 7) + 1.0)
        flap = abs(math.sin(self.cyc(B, .5)))
        w = 3.0 + 4.6 * flap
        dx, dy = wx - x, wy - y
        up = ((np.abs(dx) / w) ** 2 + ((dy + 1.6) / 3.6) ** 2) <= 1          # fore wings
        lo = ((np.abs(dx) / (w * .7)) ** 2 + ((dy - 2.0) / 2.6) ** 2) <= 1   # hind wings
        wing = (up | lo) & (np.abs(dx) > .5)
        edge = wing & ~((((np.abs(dx) / (w * .8)) ** 2 + ((dy + 1.6) / 2.9) ** 2) <= 1) | (((np.abs(dx) / (w * .55)) ** 2 + ((dy - 2.0) / 2.0) ** 2) <= 1))
        spot = wing & (np.hypot(np.abs(dx) - w * .62, dy + 2.2) < .9)
        self.put(wing, (1.0, .55, .10), .2, .3, .1, 20)
        self.put(edge, (.10, .06, .04), .1, .3, .1, 20)
        self.put(spot, (.98, .96, .92), .85, .3, .1, 20)
        self.put((np.abs(dx) <= .6) & (np.abs(dy) < 3.4), (.10, .07, .05), .05, .32, .1, 20)

    def _bee(self, B):
        x, y, vis, perch, fx = self.bee_state(B)
        if not vis: return
        wx, wy = self.wx, self.wy; dx, dy = (wx - x) * fx, wy - y
        open_ = (math.floor(B * 4) % 2 == 0) if perch < .5 else (math.floor(B * 2) % 3 == 0)
        wr = 3.2 if open_ else 2.2
        wings = (((dx + .8) / (wr * 1.3)) ** 2 + ((dy + 4.2) / (wr * .7)) ** 2) <= 1
        self.put(wings, (.90, .94, 1.0), .45, .5, .1, 12)
        body = (dx / 5.4) ** 2 + (dy / 3.6) ** 2 <= 1
        stripe = body & (np.sin(dx * 1.6) > .35)
        self.put(body, (.96, .78, .14), .15, .55, .1, 12)
        self.put(stripe, (.08, .07, .06), .1, .55, .1, 12)
        head = ((dx - 5.6) / 2.2) ** 2 + (dy / 2.2) ** 2 <= 1
        self.put(head, (.12, .10, .08), .1, .55, .1, 12)

    def _dog(self, lb):
        k = ease((lb - 5.5) / 1.0, "outCubic") * (1 - ease((lb - 8.6) / .8, "inOutSine"))
        if k <= 0: return
        wx, wy = self.wx, self.wy
        x = -96 + 26 * k; y = 84 + .8 * math.sin(lb * TAU * 2)
        muzzle = (((wx - x) / 15) ** 2 + ((wy - y) / 7.5) ** 2 <= 1) & (wx < x + 13)
        self.put(muzzle, (.62, .40, .22), .1, .8, .06, 23)
        self.put(muzzle & (wy > y + 2.5), (.80, .62, .42), .1, .8, .06, 23)
        nose = ((wx - x - 11) / 3.6) ** 2 + ((wy - y + 1.5) / 2.8) ** 2 <= 1
        self.put(nose, (.08, .06, .06), .05, .7, .05, 23)
        self.put(np.hypot(wx - x - 10, wy - y + 2.8) < .8, (.75, .75, .80), .2, .7, .05, 23)

    def _snake(self, lb, B):
        k = ease((lb - 1.0) / 1.5, "outCubic") * (1 - ease((lb - 9.5) / .5, "inOutSine"))
        if k <= 0: return
        wx, wy = self.wx, self.wy
        x = 112 - 22 * k; y = 94
        neck = (wx > x) & (np.abs(wy - y - 1.5 * np.sin((wx - x) / 5)) < 3.4)
        head = ((wx - x) / 7.5) ** 2 + ((wy - y) / 4.5) ** 2 <= 1
        pat = np.sin(wx * .9) * np.sin(wy * .9) > .3
        c = np.where(pat[..., None], np.asarray((.30, .26, .14), np.float32), np.asarray((.52, .48, .28), np.float32))
        self.put(neck | head, c, .1, .45, .07, 24)
        self.put(np.hypot(wx - x + 3.5, wy - y + 1.6) < .9, (.05, .04, .03), .05, .36, .07, 24)     # eye
        self.put(np.hypot(wx - x + 5.6, wy - y + .2) < .6, (.02, .02, .02), .05, .36, .07, 24)      # heat pit
        if (B * 2) % 1.0 < .45:
            tg = (wx < x - 7) & (wx > x - 12) & (np.abs(wy - y - .8 - np.where(wx < x - 10, (x - 10 - wx) * .8 * np.sign(np.sin(wx * 9)), 0)) < .45)
            self.put(tg, (.85, .15, .20), .05, .36, .07, 24)

    def _fireflies(self, cv, B):
        for k in range(7):
            x = -70 + k * 23 + 6 * math.sin(self.cyc(B, 8.0) + k * 1.3)
            y = 10 + 22 * ((k * .37) % 1) + 4 * math.sin(self.cyc(B, 4.0) + k)
            on = .5 + .5 * math.sin(self.cyc(B, 2.0) + k * 2.2)
            if on < .35: continue
            m = np.hypot(self.wx - x, self.wy - y) < .9
            self.put(m, (.85, 1.0, .55), .1, .3, .3, 25); self.emit |= m
            cv.glow(x, y, 3.5, (.6, .9, .4), .5 * on)


CROPS = {"flower": (-44, -10, 46, 95)}     # named crops (world box x0, y0, x1, y1); tile size = box size


class VisionMosaic(Scene):
    """Six tiles of the same living world through six eyes (2×3, staggered pop-in, 1-px Kutu gutters)."""
    final = True
    defaults = {"tiles": ["insan", "ari", "kopek", "yilan", "yarasa", "mantis12"], "grid": [2, 3], "stagger_beats": .25,
                "crop": [-44, -10, 46, 95], "time": "day", "gutter": "#04060E",
                "lead": 2, "empty_dim": .42, "sonar_base": .3,
                # QC: a thermal tile cropped on the (cold) flower was one flat violet. Thermal cameras show heat with
                # automatic gain (contrast stretched over the frame's own range) → same relative heat, readable tile.
                "thermal_agc": [3, 99.7], "thermal_blur": 1.2}

    def attach(self, film):
        from .raster import Canvas
        self.film = film
        crop = self.p["crop"] if isinstance(self.p["crop"], (list, tuple)) else CROPS.get(self.p["crop"], CROPS["flower"])
        x0, y0, x1, y1 = crop; self.cw, self.ch = int(round(x1 - x0)), int(round(y1 - y0))
        self.ccx, self.ccy = (x0 + x1) / 2, (y0 + y1) / 2
        self.world = VisionWorld({"time": self.p["time"], "focus": "flower"}, 0, film.world_pal).bind(self._seg, film.s)
        self.world.attach(film)
        self.tcv = Canvas(self.cw, self.ch, film.world_pal); self.tcv.enable_aux()
        from . import vision as V
        self.modes = [V.resolve(film.s, m) for m in self.p["tiles"]]

    def bind(self, seg, spec):
        self._seg = seg; return super().bind(seg, spec)

    def focus(self, lb, dur_b): return ANCHORS["flower"]

    def draw(self, cv, lt, lb, dur_b):          # validator / non-film use: plain world
        VisionWorld({"time": self.p["time"]}, 0, self.pal).bind(self._seg, {"total_beats": self.total, "loop": self.loop}).draw(cv, lt, lb, dur_b)

    def final_image(self, cv, lt, lb, dur_b, t_abs):
        from . import vision as V
        from .raster import Camera
        f = self.film; H, W = cv.H, cv.W
        gut = np.array([int(self.p["gutter"][i:i + 2], 16) for i in (1, 3, 5)], np.uint8)
        out = np.zeros((H, W, 3), np.uint8); out[:] = gut
        z = cv.cam.zoom
        self.tcv.set_cam(Camera(self.ccx, self.ccy, z, 0.0)); self.tcv.pal = f.world_pal; self.tcv.clear()
        self.world.draw(self.tcv, lt, lb, dur_b)
        G = {"rgb": np.clip(self.tcv.rgb + self.tcv.glowbuf, 0, 1), **self.tcv.aux}
        bx, by = self.tcv.to_screen(*ANCHORS["bat"])
        ctx = {"origin": (float(bx), float(by)), "rings": f.sonar_rings({"rings_on": "drum:B", "persistence_beats": 1.5}, self.b0 + lb),
               "base": float(self.p.get("sonar_base", .3))}
        cols, rows = self.p["grid"]; tw = (W - (cols - 1)) // cols; th = (H - (rows + 1)) // rows
        fk = f._flash(t_abs) if t_abs is not None else 0.0
        st = max(float(self.p["stagger_beats"]), 1e-6); lead = int(self.p.get("lead", 2))
        base = None
        for k, m in enumerate(self.modes):
            # tiles 0..lead-1 are already in on the first frame (no empty/black opening frame); the rest pop in
            # every `stagger_beats`; a slot that is not in yet shows the first eye, dimmed (palette-safe)
            share = (lb - (k - lead) * st) / st if k >= lead else 1.0
            if share <= 0 or share < 1:
                if base is None:
                    m0 = self.modes[0]
                    base = V.quantize(V.apply(m0, G, ctx) * float(self.p.get("empty_dim", .42)), m0.pal, m0.pixel, m0.spread)
            if share <= 0: img = base
            else:
                d = V.apply(*self._tile_mode(m, G), ctx)
                if fk > 0: d = (d + np.asarray(m.pal.ramp("energy", 1.0)) * fk) * (1 + .3 * fk)
                img = V.quantize(d, m.pal, m.pixel, m.spread)
                if share < 1: img = V.dither_mix(base, img, share)
                share = 1.0
            r_, c_ = divmod(k, cols)
            x0 = c_ * (tw + 1); y0 = 1 + r_ * (th + 1)
            ww = min(tw + (1 if c_ == cols - 1 and (W - (cols - 1)) % cols else 0), self.cw); hh = min(th, self.ch)
            ox = (self.cw - ww) // 2; oy = (self.ch - hh) // 2
            out[y0:y0 + hh, x0:x0 + ww] = img[oy:oy + hh, ox:ox + ww]
        return out

    def _tile_mode(self, m, G):
        """(mode, G-buffer) for one tile: thermal tiles get auto-gain on temp (+ their own blur), others unchanged."""
        agc = self.p.get("thermal_agc")
        if m.map != "thermal" or not agc: return m, G
        import copy
        t = G["temp"]; lo, hi = np.percentile(t, agc)
        mm = copy.copy(m); mm.blur = float(self.p.get("thermal_blur", m.blur))
        return mm, {**G, "temp": (.05 + .95 * np.clip((t - lo) / max(hi - lo, 1e-3), 0, 1)).astype(np.float32)}


SCENES.update({"vision_world": VisionWorld, "vision_mosaic": VisionMosaic})
