import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "bitloop"))  # repo-relative engine
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from bitloop import spec as S
from bitloop.render import Film
from bitloop.palette import Palette, HAYRET_NAMES, PALETTES
from bitloop.pixfont import MARK, line_bitmap
from bitloop.captions import CaptionStyle, render as cap_render

OUT = os.path.abspath(os.path.join(_HERE, ".."))  # brand/
pal = Palette("hayret")
hexs = list(HAYRET_NAMES)
C = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
BG, CREAM, TURQ, CORAL = C("#060814"), C("#F4ECDC"), C("#41E8D2"), C("#FF9A86")
DJ = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"; DJB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F = lambda n, b=False: ImageFont.truetype(DJB if b else DJ, n)

W, H = 2400, 1640
im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
# subtle tile pattern background
for y in range(0, H, 48):
    for x in range(0, W, 48):
        if (x // 48 + y // 48) % 2 == 0: d.rectangle([x + 22, y + 22, x + 25, y + 25], fill=C("#0B1230"))

def pixtext(text, x, y, dot, col, anchor="l"):
    m, _ = line_bitmap([(text, False)])
    h_, w_ = m.shape
    if anchor == "c": x -= w_ * dot // 2
    for yy, xx in zip(*np.nonzero(m)):
        d.rectangle([x + xx * dot, y + yy * dot, x + xx * dot + dot - 1, y + yy * dot + dot - 1], fill=col)
    return w_ * dot

def mark(x, y, dot):
    cols = {"o": CREAM, "t": TURQ, "c": C("#EC4A57"), "k": BG, "s": C("#D2FFF5")}
    for r, row in enumerate(MARK):
        for c, ch in enumerate(row):
            if ch in cols: d.rectangle([x + c * dot, y + r * dot, x + c * dot + dot - 1, y + r * dot + dot - 1], fill=cols[ch])

# ---- header
mark(60, 50, 14)
pixtext("hayret.piksel", 300, 70, 12, CREAM)
d.text((304, 200), "MARKA KILAVUZU · v1  —  “Çini Gecesi”: kobalt gece, türkuaz hayret, mercan ısı, krem ışık", font=F(30), fill=C("#B8CDF2"))
d.text((304, 245), "Sinyal: göz + “!” = hayret anı.  Ses: her videoda konuya özel chiptune + sabit 4 notalık ses logosu.", font=F(26), fill=C("#77A2EE"))

# ---- palette
px, py = 60, 320
d.text((px, py), "PALET  (17 renk)", font=F(30, True), fill=CREAM)
roles = {"Gece": "zemin", "Derin Lacivert": "zemin", "Mürekkep": "zemin / gölge", "Kobalt Koyu": "orta ton",
         "Kobalt": "orta ton (gövde)", "Lapis": "orta ton", "Gök": "açık ton", "Sis": "parlak ton", "Krem": "ışık · yazı",
         "Derin Firuze": "hayret gölgesi", "Firuze": "hayret", "Türkuaz Işık": "HAYRET · kilit sayı", "Parıltı": "kıvılcım",
         "Kiremit": "ısı gölgesi", "Çini Mercanı": "ısı · gerilim · '!'", "Mercan Işık": "neon · vurgu 2", "Kutu": "altyazı kutusu"}
sw = 84
for i, h in enumerate(hexs):
    cx, cy = px + (i % 4) * 238, py + 50 + (i // 4) * 104
    d.rectangle([cx, cy, cx + sw, cy + sw], fill=C(h), outline=C("#2C47A6"))
    d.text((cx + sw + 10, cy + 4), HAYRET_NAMES[h], font=F(17, True), fill=CREAM)
    d.text((cx + sw + 10, cy + 30), h, font=F(18), fill=C("#B8CDF2"))
    d.text((cx + sw + 10, cy + 54), roles[HAYRET_NAMES[h]], font=F(15), fill=C("#77A2EE"))

# ---- caption sample + contrast
cx0 = 1010
d.text((cx0, 320), "ALTYAZI  (5×7 piksel font, Türkçe büyük harf)", font=F(30, True), fill=CREAM)
st = CaptionStyle(1080, 1920, pal)
arr, _, _, _ = cap_render("GÖZÜNÜ AÇ:\nHER ŞEY\n*%100 HAYRET*", st)
cap = Image.fromarray(arr[..., :3])
_fb = Film(S.load(os.path.join(OUT, "src", "samples.json")))
bgcrop = Image.fromarray(_fb.frame(23.5)).crop((0, 700, 1080, 1300)).resize((540, 300))
panel = bgcrop.copy(); scale = .5
cap_s = cap.resize((int(cap.width * scale), int(cap.height * scale)), Image.NEAREST)
panel.paste(cap_s, ((540 - cap_s.width) // 2, 20))
im.paste(panel, (cx0, 375)); d.rectangle([cx0, 375, cx0 + 540, 675], outline=C("#2C47A6"))
d.text((cx0 + 560, 380), "kutu #04060E · metin Krem #F4ECDC (17.2:1)\nkilit sayı Türkuaz Işık #41E8D2 (13.2:1)\nvurgu 2 Mercan Işık #FF9A86 (9.8:1)\nhepsi WCAG AAA (≥ 7:1)", font=F(22), fill=C("#B8CDF2"), spacing=10)
d.text((cx0 + 560, 540), "üstte ortalı · ≤3 satır · ≤12 harf/satır\n0.1 sn dither'lı giriş/çıkış · İ Ş Ğ Ü Ö Ç tam boy", font=F(20), fill=C("#77A2EE"), spacing=8)

# ---- logo + sonic logo
d.text((cx0, 700), "İŞARET  “hayret gözü”  ·  SES LOGOSU", font=F(30, True), fill=CREAM)
mark(cx0, 760, 10)
d.text((cx0 + 170, 765), "göz = merak · göz bebeği “!” = hayret anı\n3 kıvılcım = keşif. Tek renk (damga, kazıma)\nveya tam renk (neon, etiket) kullanılır.", font=F(20), fill=C("#B8CDF2"), spacing=8)
# notation of the sonic logo
nx, ny = cx0 + 760, 760
notes = [("La", 0, .5), ("Re", 1, .5), ("Mi♭", 2, .5), ("Fa♯", 3, 1.75)]
heights = [0, 3, 4, 7]
for i, (n, k, du) in enumerate(notes):
    x = nx + i * 90; y = ny + 100 - heights[i] * 12
    w = 70 if du < 1 else 170
    d.rectangle([x, y, x + w, y + 18], fill=TURQ if i < 3 else CORAL)
    d.text((x, y + 24), n, font=F(20, True), fill=CREAM)
d.text((nx - 40, ny + 165), "5 → 1 → 2 → 3 · kısa-kısa-kısa-UZUN\nher videonun anahtarına transpoze\n(örn. Re Hicaz: La–Re–Mi♭–Fa♯)\nifşada ve döngü dikişinde", font=F(19), fill=C("#77A2EE"), spacing=6)

# ---- stills
labels = ["Kavanoz etiketi\n(okunur ana yerleşim)", "Uzay aracı gövdesi", "Neon tabela\n(şehir siluetinde)", "Terminal açılış metni",
          "Laboratuvar markası\nplakası", "Damga (vuruşta)", "Görev arması +\npil etiketi", "Kara tahta + reklam\npanosu"]
times = [3, 7, 11, 15, 19, 23.5, 27, 31]
s = S.load(os.path.join(OUT, "src", "samples.json")); f = Film(s)
y0 = 1040; tw, th = 270, 480
d.text((60, y0 - 50), "DÜNYA İÇİ ETİKET YERLEŞİMLERİ  (filigran yok — @hayret.piksel sahnenin bir parçası)", font=F(30, True), fill=CREAM)
for i, t in enumerate(times):
    fr = Image.fromarray(f.frame(t)).resize((tw, th), Image.LANCZOS)
    x = 60 + i * (tw + 22)
    im.paste(fr, (x, y0)); d.rectangle([x - 1, y0 - 1, x + tw, y0 + th], outline=C("#2C47A6"))
    d.text((x, y0 + th + 10), labels[i], font=F(19), fill=C("#B8CDF2"), spacing=4)
im.save(os.path.join(OUT, "brand_board.png"))
print(im.size)
