"""Art-resolution software rasteriser with a redraw-based camera.

Everything is drawn in WORLD units onto a small float RGB buffer (default 180x320 art pixels for 9:16).
The camera (cx, cy, zoom, rot) is applied to geometry before rasterising, so a zoom is a re-draw at a new
scale, never a bitmap stretch: pixels stay square and crisp at every zoom level. Light/glow is accumulated in
a separate additive buffer; the whole frame is then Bayer-quantised to the locked palette and nearest-upscaled.
"""
import math
import numpy as np


class Camera:
    def __init__(self, cx=0.0, cy=0.0, zoom=1.0, rot=0.0):
        self.cx, self.cy, self.zoom, self.rot = cx, cy, zoom, rot


class Canvas:
    def __init__(self, W, H, pal):
        self.W, self.H, self.pal = W, H, pal
        self.rgb = np.zeros((H, W, 3), np.float32)
        self.glowbuf = np.zeros((H, W, 3), np.float32)
        self.cam = Camera()
        self.ys, self.xs = np.mgrid[0:H, 0:W].astype(np.float32) + 0.5
        self.aux = None            # vision G-buffer planes (uv, temp, depth, oid), allocated by enable_aux()

    # ---------- vision G-buffer (aux planes) ----------
    AUX_CLEAR = {"uv": 0.0, "temp": 0.0, "depth": 1.0, "oid": 0}

    def enable_aux(self):
        """Allocate the aux planes a vision pass reads: uv (0..1 UV reflectance), temp (0..1 heat), depth (0 near .. 1
        sky/far) and oid (int object id, 0 = sky/background). Scenes write them with put_aux(); everything else gets
        stage defaults from Film (see render.Film._aux_stage)."""
        if self.aux is None:
            self.aux = {"uv": np.zeros((self.H, self.W), np.float32), "temp": np.zeros((self.H, self.W), np.float32),
                        "depth": np.ones((self.H, self.W), np.float32), "oid": np.zeros((self.H, self.W), np.int32)}
        return self.aux

    def clear_aux(self):
        if self.aux is not None:
            for k, v in self.aux.items(): v[:] = self.AUX_CLEAR[k]

    def put_aux(self, mask, uv=None, temp=None, depth=None, oid=None):
        """Write aux channels where mask (bool or 0..1 coverage ≥ .5) is set; each value is a scalar or a full-frame array."""
        if self.aux is None: return
        m = mask if mask.dtype == bool else mask >= .5
        if not m.any(): return
        for k, v in (("uv", uv), ("temp", temp), ("depth", depth), ("oid", oid)):
            if v is None: continue
            self.aux[k][m] = v if np.isscalar(v) else np.asarray(v)[m]

    # ---------- camera ----------
    def set_cam(self, cam):
        self.cam = cam
        self._c, self._s = math.cos(cam.rot), math.sin(cam.rot)

    def to_screen(self, x, y):
        c = self.cam
        dx, dy = np.asarray(x, np.float32) - c.cx, np.asarray(y, np.float32) - c.cy
        X = (self._c * dx - self._s * dy) * c.zoom + self.W / 2
        Y = (self._s * dx + self._c * dy) * c.zoom + self.H / 2
        return X, Y

    def sl(self, r):  # world length -> screen length
        return r * self.cam.zoom

    def _box(self, X, Y, R):
        x0, x1 = max(0, int(X - R - 1)), min(self.W, int(X + R + 2))
        y0, y1 = max(0, int(Y - R - 1)), min(self.H, int(Y + R + 2))
        if x0 >= x1 or y0 >= y1:
            return None
        return slice(y0, y1), slice(x0, x1)

    @staticmethod
    def _col(c):
        return np.asarray(c, np.float32).reshape(1, 1, 3) if not isinstance(c, np.ndarray) or c.ndim == 1 else c

    def _blend(self, b, mask, col):
        if mask.max() <= 0:
            return
        m = mask[..., None]
        self.rgb[b] = self.rgb[b] * (1 - m) + col * m

    # ---------- primitives ----------
    def clear(self, top=None, bottom=None):
        r = self.pal.bg
        top = r[1] if top is None else top
        bottom = r[0] if bottom is None else bottom
        t = (self.ys / self.H)[..., None]
        self.rgb[:] = np.asarray(top) * (1 - t) + np.asarray(bottom) * t
        self.glowbuf[:] = 0
        self.clear_aux()
        self.keep = None

    def disc(self, x, y, r, color, alpha=1.0):
        X, Y = self.to_screen(x, y); R = max(self.sl(r), 0.5)
        b = self._box(X, Y, R)
        if b is None: return
        d = np.hypot(self.xs[b] - X, self.ys[b] - Y)
        self._blend(b, (d <= R).astype(np.float32) * alpha, self._col(color))

    def sphere(self, x, y, r, ramp="body", light=(-0.55, -0.65), rim=None, alpha=1.0, spec=True, tone=1.0):
        """Pseudo-3D shaded ball: lambert along a palette ramp, optional amber rim light + specular dot."""
        X, Y = self.to_screen(x, y); R = self.sl(r)
        if R < 0.6:
            return self.disc(x, y, r, self.pal.ramp(ramp, 0.75 * tone), alpha)
        b = self._box(X, Y, R)
        if b is None: return
        nx, ny = (self.xs[b] - X) / R, (self.ys[b] - Y) / R
        d2 = nx * nx + ny * ny; inside = d2 <= 1
        nz = np.sqrt(np.clip(1 - d2, 0, 1))
        lx, ly = light; lz = math.sqrt(max(0, 1 - lx * lx - ly * ly))
        lam = np.clip(nx * lx + ny * ly + nz * lz, 0, 1)
        shade = np.clip((0.15 + 0.85 * lam) * tone, 0, 1)
        col = self.pal.ramp(ramp, shade)
        if rim is not None:
            rimk = np.clip((np.sqrt(d2) - 0.78) / 0.22, 0, 1) * np.clip(nx * -lx + ny * -ly + 0.3, 0, 1)
            col = col * (1 - rimk[..., None]) + np.asarray(rim, np.float32) * rimk[..., None]
        if spec and R >= 3:
            sp = (np.hypot(nx - lx * 0.55, ny - ly * 0.55) < max(0.16, 0.9 / R)).astype(np.float32)
            col = col * (1 - sp[..., None]) + self.pal.ramp(ramp, 1.0) * sp[..., None]
        m = inside.astype(np.float32) * alpha
        self.rgb[b] = self.rgb[b] * (1 - m[..., None]) + col * m[..., None]

    def _seg_dist(self, b, X0, Y0, X1, Y1):
        px, py = self.xs[b], self.ys[b]
        vx, vy = X1 - X0, Y1 - Y0; L2 = vx * vx + vy * vy + 1e-9
        t = np.clip(((px - X0) * vx + (py - Y0) * vy) / L2, 0, 1)
        qx, qy = X0 + t * vx, Y0 + t * vy
        return np.hypot(px - qx, py - qy), (px - qx), (py - qy), t

    def capsule(self, x0, y0, x1, y1, r, ramp="pale", light=(-0.55, -0.65), alpha=1.0, flat=None, tone=1.0):
        """Shaded tube/capsule between two world points (myelin, rods, branches). flat=colour draws a plain line."""
        X0, Y0 = self.to_screen(x0, y0); X1, Y1 = self.to_screen(x1, y1); R = max(self.sl(r), 0.5)
        x_lo, x_hi = min(X0, X1), max(X0, X1); y_lo, y_hi = min(Y0, Y1), max(Y0, Y1)
        b = self._box((x_lo + x_hi) / 2, (y_lo + y_hi) / 2, max(x_hi - x_lo, y_hi - y_lo) / 2 + R)
        if b is None: return
        d, ex, ey, _ = self._seg_dist(b, X0, Y0, X1, Y1)
        inside = (d <= R).astype(np.float32) * alpha
        if flat is not None or R < 1.2:
            col = self._col(flat if flat is not None else self.pal.ramp(ramp, 0.7 * tone))
            return self._blend(b, inside, col)
        nx, ny = ex / R, ey / R; nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
        lx, ly = light; lz = math.sqrt(max(0, 1 - lx * lx - ly * ly))
        lam = np.clip(nx * lx + ny * ly + nz * lz, 0, 1)
        col = self.pal.ramp(ramp, np.clip((0.15 + 0.85 * lam) * tone, 0, 1))
        self.rgb[b] = self.rgb[b] * (1 - inside[..., None]) + col * inside[..., None]

    def line(self, x0, y0, x1, y1, w, color, alpha=1.0):
        self.capsule(x0, y0, x1, y1, w / 2, flat=color, alpha=alpha)

    def polyline(self, pts, r, ramp="pale", flat=None, alpha=1.0, tone=1.0):
        for (a, b_), (c, d) in zip(pts[:-1], pts[1:]):
            self.capsule(a, b_, c, d, r, ramp=ramp, flat=flat, alpha=alpha, tone=tone)

    def ring(self, x, y, r, w, color, alpha=1.0, dashes=0, phase=0.0, duty=0.6):
        X, Y = self.to_screen(x, y); R = self.sl(r); Wd = max(self.sl(w), 1.0)
        b = self._box(X, Y, R + Wd)
        if b is None: return
        dx, dy = self.xs[b] - X, self.ys[b] - Y
        m = (np.abs(np.hypot(dx, dy) - R) <= Wd / 2).astype(np.float32)
        if dashes:
            a = (np.arctan2(dy, dx) / (2 * math.pi) * dashes + phase) % 1.0
            m *= (a < duty)
        self._blend(b, m * alpha, self._col(color))

    def glow(self, x, y, r, color, k=1.0):
        """Additive soft light (becomes dithered bloom after quantisation)."""
        X, Y = self.to_screen(x, y); R = max(self.sl(r), 1.0)
        b = self._box(X, Y, R * 2.2)
        if b is None: return
        d2 = ((self.xs[b] - X) ** 2 + (self.ys[b] - Y) ** 2) / (R * R)
        self.glowbuf[b] += np.exp(-d2 * 1.6)[..., None] * np.asarray(color, np.float32) * k

    def points(self, xs, ys, color, alpha=1.0, size=1):
        """Particles: one art pixel (or size×size) each, colour per point allowed."""
        X, Y = self.to_screen(xs, ys)
        X = np.floor(np.atleast_1d(X)).astype(int); Y = np.floor(np.atleast_1d(Y)).astype(int)
        col = np.asarray(color, np.float32)
        if col.ndim == 1: col = np.broadcast_to(col, (len(X), 3))
        al = np.broadcast_to(np.asarray(alpha, np.float32), (len(X),))
        for oy in range(size):
            for ox in range(size):
                xx, yy = X + ox, Y + oy
                ok = (xx >= 0) & (xx < self.W) & (yy >= 0) & (yy < self.H)
                a = al[ok][:, None]
                self.rgb[yy[ok], xx[ok]] = self.rgb[yy[ok], xx[ok]] * (1 - a) + col[ok] * a

    def image(self, img, x, y, h, alpha=1.0):
        """Blit an RGBA float image (0..1) centred at world (x,y) with world height h (nearest sampling of source)."""
        X, Y = self.to_screen(x, y); Hs = self.sl(h); ih, iw = img.shape[:2]; Ws = Hs * iw / ih
        b = self._box(X, Y, max(Ws, Hs) / 2 * 1.5)
        if b is None: return
        # inverse map (handles camera rotation too)
        px, py = self.xs[b] - X, self.ys[b] - Y
        u = (self._c * px + self._s * py) / Hs * ih + iw / 2
        v = (-self._s * px + self._c * py) / Hs * ih + ih / 2
        ok = (u >= 0) & (u < iw) & (v >= 0) & (v < ih)
        ui, vi = np.clip(u.astype(int), 0, iw - 1), np.clip(v.astype(int), 0, ih - 1)
        s = img[vi, ui]; a = s[..., 3] * ok * alpha
        self.rgb[b] = self.rgb[b] * (1 - a[..., None]) + s[..., :3] * a[..., None]

    def mask_fill(self, mask_fn, color, alpha=1.0):
        """Fill screen pixels where mask_fn(world_x, world_y) is True (used for silhouettes/objects)."""
        c = self.cam
        dx, dy = (self.xs - self.W / 2) / c.zoom, (self.ys - self.H / 2) / c.zoom
        wx = self._c * dx + self._s * dy + c.cx; wy = -self._s * dx + self._c * dy + c.cy
        m = mask_fn(wx, wy).astype(np.float32) * alpha
        self._blend((slice(None), slice(None)), m, self._col(color))

    def world_grid(self):
        c = self.cam
        dx, dy = (self.xs - self.W / 2) / c.zoom, (self.ys - self.H / 2) / c.zoom
        return self._c * dx + self._s * dy + c.cx, -self._s * dx + self._c * dy + c.cy

    def vignette(self, k=0.42):
        nx, ny = (self.xs / self.W - 0.5) * 2, (self.ys / self.H - 0.5) * 2
        v = np.clip(1 - k * (nx * nx * 0.8 + ny * ny * 0.6), 0.25, 1)
        keep = getattr(self, "keep", None)          # legible tag pixels (render._matte_glow): flat paint, no edge falloff
        if keep is not None: v = np.where(keep, 1.0, v)
        self.rgb *= v[..., None]

    def composite(self, spread=0.11):
        out = np.clip(self.rgb + self.glowbuf, 0, 1)
        return self.pal.quantize(out, spread)


def _poly_mask_impl(cv, pts, outline_only=False, width=1):
    """Screen-space bool mask of a world-space polygon (PIL rasteriser, pixel-centre exact, fast for 1000s of edges)."""
    from PIL import Image, ImageDraw
    P = np.asarray(pts, np.float64)
    X, Y = cv.to_screen(P[:, 0], P[:, 1])
    im = Image.new("1", (cv.W, cv.H), 0); d = ImageDraw.Draw(im)
    xy = list(zip((np.asarray(X) - .5).tolist(), (np.asarray(Y) - .5).tolist()))
    if outline_only: d.line(xy + xy[:1], fill=1, width=width)
    else: d.polygon(xy, fill=1)
    return np.asarray(im, bool)


def _poly(self, pts, color, alpha=1.0):
    """Filled polygon in world coords (any vertex count)."""
    m = _poly_mask_impl(self, pts).astype(np.float32) * alpha
    self._blend((slice(None), slice(None)), m, self._col(color))


def _poly_outline(self, pts, color, alpha=1.0, width=1, closed=True):
    """1-px (screen) crisp outline of a world polyline/polygon."""
    from PIL import Image, ImageDraw
    P = np.asarray(pts, np.float64); X, Y = self.to_screen(P[:, 0], P[:, 1])
    xy = list(zip((np.asarray(X) - .5).tolist(), (np.asarray(Y) - .5).tolist()))
    if closed: xy = xy + xy[:1]
    im = Image.new("1", (self.W, self.H), 0); ImageDraw.Draw(im).line(xy, fill=1, width=width)
    m = np.asarray(im, np.float32) * alpha
    self._blend((slice(None), slice(None)), m, self._col(color))


def _ellipse(self, x, y, rx, ry, color, alpha=1.0, ang=0.0):
    """Filled (rotated) ellipse in world units, pixel-centre sampled (note heads, records, labels)."""
    X, Y = self.to_screen(x, y); R = max(self.sl(max(rx, ry)), .5)
    b = self._box(X, Y, R + 1)
    if b is None: return None
    a = ang + self.cam.rot; c, s = math.cos(a), math.sin(a)
    dx, dy = self.xs[b] - X, self.ys[b] - Y
    u = (c * dx + s * dy) / max(self.sl(rx), .5); v = (-s * dx + c * dy) / max(self.sl(ry), .5)
    m = (u * u + v * v <= 1).astype(np.float32) * alpha
    self._blend(b, m, self._col(color))
    return b


def _rect_fill(self, x, y, w, h, color, alpha=1.0):
    """Axis-aligned (world) rectangle, follows camera rotation."""
    X, Y = self.to_screen(x, y); b = self._box(X, Y, self.sl(math.hypot(w, h)) / 2 + 1)
    if b is None: return
    c = self.cam; dx, dy = (self.xs[b] - self.W / 2) / c.zoom, (self.ys[b] - self.H / 2) / c.zoom
    wx = self._c * dx + self._s * dy + c.cx; wy = -self._s * dx + self._c * dy + c.cy
    m = ((np.abs(wx - x) <= w / 2) & (np.abs(wy - y) <= h / 2)).astype(np.float32) * alpha
    self._blend(b, m, self._col(color))


Canvas.poly = _poly
Canvas.poly_outline = _poly_outline
Canvas.ellipse = _ellipse
Canvas.rect = _rect_fill


def _matte(self, x, y, w, h, k=1.0):
    """Clear the additive light buffer under a world rectangle (matte paper / printed labels must not bloom)."""
    X, Y = self.to_screen(x, y); b = self._box(X, Y, self.sl(math.hypot(w, h)) / 2 + 1)
    if b is None: return
    c = self.cam; dx, dy = (self.xs[b] - self.W / 2) / c.zoom, (self.ys[b] - self.H / 2) / c.zoom
    wx = self._c * dx + self._s * dy + c.cx; wy = -self._s * dx + self._c * dy + c.cy
    m = ((np.abs(wx - x) <= w / 2) & (np.abs(wy - y) <= h / 2))
    self.glowbuf[b][m] *= 1 - k


Canvas.matte = _matte
