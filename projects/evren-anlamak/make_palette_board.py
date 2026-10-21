"""palette_board.png: the same sample frame (network cosmic web + chalkboard prop + narration) rendered by the ENGINE
in each topic palette (bitloop still), plus swatches. Run from this folder."""
import json, copy, os, subprocess, sys, tempfile
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "../../bitloop")
from bitloop.palette import PALETTES as BP
from palettes import PALETTES
TMP = tempfile.mkdtemp(prefix="ep_")
base = json.load(open("spec_proxy.json")); names = ["kozmos", "kara_tahta", "hayret"]
for n in names:
    s = copy.deepcopy(base); s["palette"] = PALETTES.get(n, "hayret")
    s["segments"] = [{"id": "S1", "role": "hook", "scene": "network", "beats": 8, "params": {"nodes": 320, "extent": 440, "wave_every": 8.0, "arcs": 3},
        "layers": {"back": ["stars", "nebula", "horizon"], "front": ["dust", "bokeh"]}, "transition_in": "cut",
        "props": [{"kind": "chalkboard", "x": 0, "y": 40, "s": 1.0, "layer": "mid", "par": 1.0, "from": 0, "lines": ["GÖRELİLİK", "+ KUANTUM", "= ?"]}],
        "narration": [{"text": "Evrenin *her* kuralını _bilseydik_?", "at": 0, "until": 8, "place": "top", "size": "head", "reveal": "none"}], "events": []}]
    s["music"]["sections"] = [{"name": "a", "beats": 8, "energy": 2}]; s["loop"] = False
    json.dump(s, open(f"{TMP}/{n}.json", "w"), ensure_ascii=False)
    subprocess.run(["./bitloop.sh", "still", f"{TMP}/{n}.json", "-t", "3", "-o", f"{TMP}/{n}.png"], cwd="../../bitloop", check=True, capture_output=True)

def _board_font(size):
    """Label font for review boards only (ASCII labels; on-screen Turkish text always uses the engine's own pixel font).
    Override with BOARD_FONT=/path/to.ttf; falls back to Pillow's default font."""
    for p in (os.environ.get("BOARD_FONT"), "/usr/share/fonts/truetype/sand-box/google/Press Start 2P/PressStart2P-Regular.ttf",
              os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "bitloop", "bitloop", "assets", "PressStart2P-Regular.ttf")):
        if p and os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)
f = _board_font(16); sm = _board_font(10)
w, h = 540, 960
B = Image.new("RGB", (3 * (w + 30) + 30, h + 420), (4, 6, 14)); d = ImageDraw.Draw(B)
d.text((30, 20), "evren-anlamak - topic palettes (engine stills, per-segment 'palette')", font=f, fill=(244, 236, 220))
use = {"kozmos": "S1, S5-S8, S10", "kara_tahta": "S2-S4 (kurallar)", "hayret": "S9 (hayret ani, marka)"}
for i, n in enumerate(names):
    x0 = 30 + i * (w + 30); B.paste(Image.open(f"{TMP}/{n}.png").resize((w, h), Image.NEAREST), (x0, 80))
    d.text((x0, 56), f"{n.upper()}  - {use[n]}", font=sm, fill=(65, 232, 210))
    cols = (PALETTES[n]["colors"] if n in PALETTES else BP["hayret"]["colors"])[:30]
    for j, c in enumerate(cols):
        r, k = divmod(j, 6); sx, sy = x0 + k * 90, 80 + h + 14 + r * 50
        d.rectangle([sx, sy, sx + 84, sy + 26], fill=tuple(int(c[q:q + 2], 16) for q in (1, 3, 5))); d.text((sx, sy + 31), c, font=sm, fill=(184, 205, 242))
B.save("palette_board.png"); print("palette_board.png", B.size)
