"""MOCK of the vision-filter system (render coder: port into the engine as scene G-buffer + vision pass).
Builds one coastal-meadow scene as a G-BUFFER (albedo rgb, uv, temp, depth, object id) at art resolution
(180×320 = 1080×1920 / grid 6), renders it through every vision mode of visions.py, Bayer-quantises to that
mode's palette, and writes:
  assets/vis_<mode>.png  (180×320 stills, used by spec_proxy.json via the `image` scene)
  assets/vis_mosaic.png  (2×3 tiles: six eyes, one meadow)
  assets/vis_night.png   (dusk version in brand 'hayret' palette, Nagel scene)
  palette_board.png      (review board: every mode + swatches + hex)"""
import os, sys, math, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter, sobel
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "../../bitloop")
from bitloop.palette import PALETTES, BAYER4
from visions import VISIONS, ORDER

def _board_font(size):
    """Label font for review boards only (ASCII labels; on-screen Turkish text always uses the engine's own pixel font).
    Override with BOARD_FONT=/path/to.ttf; falls back to Pillow's default font."""
    for p in (os.environ.get("BOARD_FONT"), "/usr/share/fonts/truetype/sand-box/google/Press Start 2P/PressStart2P-Regular.ttf",
              os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "bitloop", "bitloop", "assets", "PressStart2P-Regular.ttf")):
        if p and os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)

W, H = 180, 320
def hx(h): h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)

# ------------------------------------------------------------------ G-buffer scene
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
alb = np.zeros((H, W, 3), np.float32); uv = np.zeros((H, W), np.float32)
temp = np.zeros((H, W), np.float32); depth = np.ones((H, W), np.float32); oid = np.zeros((H, W), np.int32)
rng = np.random.default_rng(7)
def put(mask, rgb, u, t, d, i):
    alb[mask] = rgb; uv[mask] = u; temp[mask] = t; depth[mask] = d if np.isscalar(d) else d[mask]; oid[mask] = i
def disk(cx, cy, r, sx=1, sy=1): return ((xx - cx) / sx) ** 2 + ((yy - cy) / sy) ** 2 <= r * r

# sky (0) — blue gradient, scatters UV, cold, no echo
sky = yy < 150
g = (yy / 150)[..., None]
alb[sky] = (np.array([.30, .55, .92]) * (1 - g) + np.array([.70, .86, 1.0]) * g)[sky]; uv[sky] = .75; temp[sky] = .04
put(disk(146, 38, 11), [1, .97, .8], 1, .25, 1, 1)                          # sun
# far hills
hill = (yy > 128 + 10 * np.sin(xx / 23 + 1) + 6 * np.sin(xx / 9)) & (yy < 160)
put(hill, [.22, .45, .30], .12, .25, .85, 2)
# meadow
mead = yy >= 150
gd = np.clip(1 - (yy - 150) / 110, .05, 1)
grass_rgb = np.stack([.20 + .08 * rng.random((H, W)), .50 + .15 * rng.random((H, W)), .16 + .06 * rng.random((H, W))], -1)
blade = (rng.random((H, W)) > .86) & mead
grass_rgb[blade] *= 1.35
alb[mead] = grass_rgb[mead]; uv[mead] = .08; temp[mead] = .32 + .04 * rng.random((H, W))[mead]; depth[mead] = (gd * .6)[mead]; oid[mead] = 3
# tree (left): trunk + canopy, bat hanging from a branch
put((xx > 9) & (xx < 21) & (yy > 70) & (yy < 215), [.36, .24, .14], .05, .36, .30, 4)
put(((xx > 18) & (xx < 52) & (abs(yy - 98 + (xx - 18) * .15) < 2.2)), [.36, .24, .14], .05, .36, .30, 4)
can = disk(24, 64, 34, 1.15, .8) | disk(50, 74, 18)
alb[can] = np.stack([.12 + .1 * rng.random((H, W)), .36 + .18 * rng.random((H, W)), .14 + .06 * rng.random((H, W))], -1)[can]
uv[can] = .1; temp[can] = .3; depth[can] = .32; oid[can] = 5
bat = disk(44, 108, 4.2, .8, 1.3) | ((abs(xx - 44) < 7) & (abs(yy - 106) < 2.5) & ((xx - 44) ** 2 < 49 - (yy - 103) ** 2 * 3))
put(bat, [.20, .14, .12], .04, .92, .28, 6)
# beehive (right, mid): wooden box + light label plate (tag carrier: "@hayret.piksel" painted in the TARGET)
put((xx > 140) & (xx < 166) & (yy > 168) & (yy < 200), [.78, .56, .30], .30, .62, .22, 7)
put((xx > 137) & (xx < 169) & (yy > 163) & (yy < 169), [.55, .38, .20], .25, .55, .22, 7)
put((xx > 144) & (xx < 162) & (yy > 176) & (yy < 184), [.96, .92, .84], .65, .55, .21, 8)
put((xx > 150) & (xx < 156) & (yy > 194) & (yy < 199), [.10, .07, .05], 0, .75, .22, 7)   # entrance (warm brood ~35°C)
# flower (centre): stem, 8 petals, yellow to humans; UV: reflecting tips, absorbing base = BULLSEYE (Koski 2014)
FX, FY = 92, 182
put((abs(xx - FX) < 1.6) & (yy > FY) & (yy < 252), [.18, .55, .2], .06, .34, .12, 9)
r = np.hypot(xx - FX, yy - FY); a = np.arctan2(yy - FY, xx - FX)
pet = (r < 9 + 15 * np.abs(np.cos(4 * a)) ** .6) & (r > 4)
put(pet, [1.0, .82, .10], 0, .40, .11, 10)
uv[pet & (r > 13)] = .92                                                    # UV-reflecting tips
put(r <= 5.5, [.45, .25, .08], 0, .42, .10, 11)                              # disc
# bee (above flower, right)
bee = disk(112, 162, 4, 1.4, 1)
put(bee, [.95, .78, .15], .15, .55, .10, 12)
alb[bee & (np.sin(xx * 1.6) > .3)] = [.08, .07, .06]
put(disk(110, 157, 3, 1.3, .7), [.92, .95, 1], .45, .5, .10, 12)           # wings
# red ball (lower left) on grass — the dog test
ball = disk(42, 236, 10)
shade = np.clip(1 - .5 * np.hypot(xx - 38, yy - 232) / 10, .45, 1)[..., None]
alb[ball] = (np.array([.92, .12, .12]) * shade)[ball]; uv[ball] = .04; temp[ball] = .33; depth[ball] = .08; oid[ball] = 13
# stone (cool) + mouse (warm) lower right
put(disk(126, 246, 9, 1.3, .8), [.55, .55, .55], .25, .14, .09, 14)
mouse = disk(150, 240, 5.5, 1.4, .9) | disk(158, 236, 3.2)
put(mouse, [.50, .44, .40], .08, 1.0, .08, 15)
put((abs(yy - 243 - (xx - 136) * .1) < .8) & (xx > 134) & (xx < 143), [.6, .45, .45], .08, .9, .08, 15)
# shore + tide pool + mantis shrimp (bottom)
sea = yy >= 262
put(sea, [.10, .42, .55], .30, .18, .18, 16)
alb[sea] *= (1 + .18 * np.sin(xx / 5 + yy / 3))[sea][..., None]
put(sea & (yy < 266), [.85, .93, .95], .5, .2, .17, 16)                      # foam line
for cx, cy, rr in [(20, 300, 14), (160, 296, 12), (60, 316, 10)]:
    put(disk(cx, cy, rr, 1.2, .7), [.38, .34, .30], .15, .2, .15, 17)
shr = (abs(yy - (288 + 3 * np.sin((xx - 72) / 6))) < 3.6) & (xx > 72) & (xx < 112)
seg_i = ((xx - 72) // 4).astype(int) % 6
cols = np.array([[.1, .75, .35], [.15, .55, .9], [.95, .3, .2], [.95, .75, .15], [.6, .2, .8], [.1, .85, .7]])
alb[shr] = cols[seg_i[shr]]; uv[shr] = .5 + .4 * (seg_i[shr] % 2); temp[shr] = .2; depth[shr] = .14; oid[shr] = 18
put(disk(114, 286, 2.2), [.95, .3, .5], .9, .2, .14, 18)                     # stalked eye

alb = np.clip(alb, 0, 1)

# ------------------------------------------------------------------ vision mappings → display rgb
def rgb2hsv(c):
    mx = c.max(-1); mn = c.min(-1); d = mx - mn + 1e-6
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
    return h, np.where(mx > 0, d / (mx + 1e-6), 0), mx
def hsv2rgb(h, s, v):
    i = np.floor(h * 6).astype(int) % 6; f = h * 6 - np.floor(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    sel = [np.stack(x, -1) for x in [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]]
    out = np.zeros(h.shape + (3,), np.float32)
    for k in range(6): out[i == k] = sel[k][i == k]
    return out

def ramp(pal, name, t):
    r = np.array([hx(c) for c in pal["ramps"][name]]); t = np.clip(t, 0, 1) * (len(r) - 1)
    i = np.minimum(t.astype(int), len(r) - 2); f = (t - i)[..., None]; return r[i] * (1 - f) + r[i + 1] * f

def edges():
    e = (np.abs(sobel(depth, 0)) + np.abs(sobel(depth, 1))) > .08
    e |= (np.abs(sobel(oid.astype(float), 0)) + np.abs(sobel(oid.astype(float), 1))) > 0
    return e

def vision(mode, t=0.4):
    pal = VISIONS[mode]["palette"] if mode in VISIONS else PALETTES[mode]
    if mode == "insan": d = alb.copy()
    elif mode == "ari":                       # R←L(green, slight red tail) G←M(blue) B←S(UV)
        L = .82 * alb[..., 1] + .18 * alb[..., 0]
        d = np.stack([L, alb[..., 2] * .95, uv], -1)
    elif mode == "kopek":                     # Machado 2009 deuteranopia (severity 1) in ~linear space
        M = np.array([[.367322, .860646, -.227968], [.280085, .672501, .047413], [-.011820, .042940, .968881]])
        lin = alb ** 2.2; d = np.clip(lin @ M.T, 0, 1) ** (1 / 2.2)
    elif mode == "yilan":
        th = gaussian_filter(temp, VISIONS[mode]["blur"])
        lum = alb @ np.array([.3, .59, .11])
        d = ramp(pal, "body", np.clip((th - .05) / .95, 0, 1) ** .9)
        d = d * .82 + .18 * lum[..., None] * ramp(pal, "pale", np.full_like(th, .3))
    elif mode == "yarasa":                    # ring from the bat; edge + iso-depth contours lit by echo
        bx, by = 44, 108; dist = np.hypot(xx - bx, yy - by); R = 60 + 220 * t
        e = edges().astype(float) + .55 * ((np.floor(depth * 10) != np.floor(np.roll(depth, 1, 0) * 10)) & (depth < .9))
        ring = np.exp(-((dist - R) / 7) ** 2); trail = np.where(dist < R, np.exp(-(R - dist) / 70), 0)
        echo = (e * (ring * 1.0 + trail * .75) + .10 * (depth < .9) * trail + .05 * (depth < .9))
        echo = np.clip(echo, 0, 1); echo[sky & (oid == 0)] *= .15
        d = ramp(pal, "body", echo) * (echo[..., None] > .02) + ramp(pal, "bg", np.zeros_like(echo)) * (echo[..., None] <= .02)
        d = d + np.exp(-((dist - R) / 2.0) ** 2)[..., None] * .25 * (depth[..., None] > .95)  # faint wavefront in empty air
    elif mode in ("mantis12", "mantis_kaba"):
        h, s, v = rgb2hsv(alb)
        hu = np.where((uv > .85) & ~sky, .80 + .12 * uv, h)   # strong UV (petal tips, shrimp) = its own violet-end band
        hu = (hu + .035 * np.sin(xx / 7 + yy / 11) * (mode == "mantis12")) % 1   # fine hue drift → many bands
        if mode == "mantis12":
            hb = np.floor(hu * 12) / 12 + 1 / 24; vb = np.clip(np.ceil(v * 3) / 3, .34, 1)
            d = hsv2rgb(hb % 1, np.full_like(h, 1.0), vb)
        else:                                  # 5 broad classes, flat (recognition, not discrimination)
            cls = np.array([hx("#E0503A"), hx("#E8C838"), hx("#4FCB6A"), hx("#3F6FD8"), hx("#B048D8")])
            k = np.digitize(hu % 1, [.06, .2, .45, .7, .9]) % 5
            d = cls[k] * np.where(v < .25, .35, 1)[..., None]
            d[s < .18] = hx("#2E2456") * .6 + .4 * (v[s < .18][..., None] > .7)
    elif mode == "hayret":                    # dusk/night, brand palette (Nagel)
        lum = alb @ np.array([.3, .59, .11]); d = lum[..., None] * np.array([.55, .7, 1.0]) * .75
        d[sky] = (np.array([.04, .06, .16]) * (1 - g) + np.array([.12, .18, .45]) * g)[sky]
    return quant(d, pal, VISIONS.get(mode, {}).get("pixel", 1))

def quant(d, pal, px=1, spread=.11):
    if px > 1:
        hh, ww = H // px, W // px
        d = d[:hh * px, :ww * px].reshape(hh, px, ww, px, 3).mean((1, 3)); d = np.repeat(np.repeat(d, px, 0), px, 1)
    cols = np.array([hx(c) for c in pal["colors"]])
    by = np.tile(BAYER4, (H // 4 + 1, W // 4 + 1))[:H, :W]
    if px > 1: by = np.repeat(np.repeat(by[::px, ::px][:H // px, :W // px], px, 0), px, 1)
    x = d + (by[..., None] - .5) * spread
    idx = ((x[:, :, None, :] - cols[None, None]) ** 2).sum(-1).argmin(-1)
    return (cols[idx] * 255 + .5).astype(np.uint8)

if __name__ == "__main__":
    out = {}
    for m in ORDER:
        out[m] = vision(m); Image.fromarray(out[m]).save(f"assets/vis_{m}.png")
    for k, t in enumerate((.15, .55, .95)):
        Image.fromarray(vision("yarasa", t)).save(f"assets/vis_yarasa_{k}.png")
    out["hayret"] = vision("hayret"); Image.fromarray(out["hayret"]).save("assets/vis_night.png")
    # mosaic: six eyes, one meadow (crop around flower+ball+mouse)
    tiles = ["insan", "ari", "kopek", "yilan", "yarasa", "mantis12"]
    cx0, cy0, tw, th = 46, 150, 90, 105
    mos = np.zeros((H, W, 3), np.uint8); mos[:] = (4, 6, 14)
    for i, m in enumerate(tiles):
        r_, c_ = divmod(i, 2); crop = out[m][cy0:cy0 + th, cx0:cx0 + tw]
        mos[1 + r_ * (th + 1): 1 + r_ * (th + 1) + th, c_ * (tw): c_ * tw + tw][:, :] = crop[:, :]
    Image.fromarray(mos).save("assets/vis_mosaic.png")
    # ---- review board
    S = 3; pw, ph = W * S, H * S
    font = _board_font(14)
    small = _board_font(9)
    panels = ORDER + ["hayret"]
    cols_n = 4; rows_n = 2; lab = 40; sw = 150
    B = Image.new("RGB", (cols_n * (pw + 20) + 20, rows_n * (ph + lab + sw + 20) + 70), (4, 6, 14)); dr = ImageDraw.Draw(B)
    dr.text((20, 22), "canli-gozu · ayni sahne, 7 goz + marka gecesi (MOCK vision filter, art 180x320 x3)", font=font, fill=(244, 236, 220))
    for i, m in enumerate(panels):
        r_, c_ = divmod(i, cols_n); x0 = 20 + c_ * (pw + 20); y0 = 70 + r_ * (ph + lab + sw + 20)
        im = Image.fromarray(out[m]).resize((pw, ph), Image.NEAREST); B.paste(im, (x0, y0 + lab))
        name = VISIONS[m]["label"] if m in VISIONS else "MARKA · Cini Gecesi (Nagel)"
        name = name.translate(str.maketrans("İıÖöÜüŞşÇçĞğ", "IiOoUuSsCcGg"))
        dr.text((x0, y0 + 12), name, font=font, fill=(65, 232, 210))
        pal = VISIONS[m]["palette"] if m in VISIONS else PALETTES["hayret"]
        cs = [c for c in pal["colors"] if c not in ("#04060E", "#F4ECDC")] if m in VISIONS else pal["colors"]
        cs = cs[:24]; per = 6; cw = pw // per
        for j, c in enumerate(cs):
            rr, cc = divmod(j, per); sx, sy = x0 + cc * cw, y0 + lab + ph + 6 + rr * 36
            dr.rectangle([sx, sy, sx + cw - 4, sy + 20], fill=tuple(int(v * 255) for v in hx(c)))
            dr.text((sx, sy + 23), c, font=small, fill=(184, 205, 242))
    B.save("palette_board.png"); print("ok", B.size)
