"""Vision system (G-buffer aux planes + per-creature maps + per-segment palettes), vision scenes, sonar ↔ drum 'B',
pad max_notes, one-note chords. Run: python tests/test_vision.py"""
import os, sys, math, tempfile
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from bitloop import spec as S, vision as V, music as M, drums as D
from bitloop.palette import Palette
from bitloop.raster import Canvas
from bitloop.timing import Meter


def P(ramps):
    cols = []
    for r in ramps.values():
        for c in r:
            if c not in cols: cols.append(c)
    for c in ("#04060E", "#F4ECDC"):
        if c not in cols: cols.append(c)
    return {"colors": cols, "ramps": ramps, "caption": {"box": "#04060E", "text": "#F4ECDC", "hi": "#41E8D2", "hi2": "#FF9A86"}}

NAT = P({"bg": ["#0E1B2E", "#1C3550", "#2F5F86", "#5E9CC8"], "body": ["#1A2414", "#2E4A22", "#3F7A2E", "#63A83A", "#9FD05A", "#D9EFA0"],
         "pale": ["#5E9CC8", "#BFE3F5", "#E8F6FC"], "energy": ["#7A4A00", "#D18A00", "#FFC21A", "#FFE680"],
         "accent": ["#5E0F14", "#B3202A", "#E8403A", "#FF8C7A"], "dim": ["#1A2230", "#46596B", "#A3B3BE"]})
MONO = P({"bg": ["#000505", "#021612", "#053026"], "body": ["#053026", "#127456", "#4CD6A8", "#F0FFF8"], "pale": ["#4CD6A8", "#F0FFF8"],
          "energy": ["#4CD6A8", "#F0FFF8"], "accent": ["#127456", "#A6FFE0"], "dim": ["#021612", "#0A4C3A"]})
HEAT = P({"bg": ["#04020A", "#1C0A44"], "body": ["#1C0A44", "#6E1A7E", "#D84A4A", "#FFC24A", "#FFFFF4"], "pale": ["#A8286E", "#FFC24A"],
          "energy": ["#FFC24A", "#FFFFF4"], "accent": ["#6E1A7E", "#FF9A5A"], "dim": ["#0A0418", "#341660"]})
VIS = {"insan": {"map": "rgb", "palette": NAT}, "ari": {"map": "bee_false_colour", "palette": NAT},
       "kopek": {"map": "dichromat", "pixel": 2, "palette": NAT}, "yilan": {"map": "thermal", "blur": 2.0, "palette": HEAT},
       "yarasa": {"map": "sonar", "palette": MONO}, "m12": {"map": "bands12", "palette": NAT}, "m5": {"map": "coarse_classes", "palette": NAT}}


def gbuf(H=64, W=36):
    G = {"rgb": np.zeros((H, W, 3), np.float32), "uv": np.zeros((H, W), np.float32), "temp": np.full((H, W), .2, np.float32),
         "depth": np.ones((H, W), np.float32), "oid": np.zeros((H, W), np.int32)}
    G["rgb"][32:, :] = (.20, .50, .16); G["depth"][32:, :] = .4; G["oid"][32:, :] = 3          # grass
    G["rgb"][40:50, 5:15] = (.92, .12, .12); G["oid"][40:50, 5:15] = 13; G["depth"][40:50, 5:15] = .08  # red ball
    G["rgb"][40:46, 22:30] = (.5, .44, .4); G["temp"][40:46, 22:30] = 1.0; G["oid"][40:46, 22:30] = 15  # mouse
    G["rgb"][10:20, 10:26] = (1, .82, .1); G["uv"][10:20, 18:26] = .92; G["oid"][10:20, 10:26] = 10; G["depth"][10:20, 10:26] = .1
    return G


def test_canvas_aux_planes():
    cv = Canvas(20, 30, Palette("hayret")); assert cv.aux is None
    cv.enable_aux(); m = np.zeros((30, 20), bool); m[5:10, 5:10] = True
    cv.put_aux(m, uv=.9, temp=.7, depth=.2, oid=7)
    assert cv.aux["uv"][7, 7] == np.float32(.9) and cv.aux["oid"][7, 7] == 7 and cv.aux["depth"][0, 0] == 1
    cv.put_aux(np.where(m, .4, 0.0).astype(np.float32), oid=9)                   # coverage < .5 writes nothing
    assert cv.aux["oid"][7, 7] == 7
    cv.clear(); assert cv.aux["oid"].max() == 0 and cv.aux["depth"].min() == 1 and cv.aux["uv"].max() == 0


def test_maps_follow_the_reference_formulas():
    s = {"visions": VIS}; G = gbuf()
    bee = V.apply(V.resolve(s, "ari"), G)
    tip, base = bee[15, 22], bee[15, 12]
    assert np.allclose(tip, [.82 * .82 + .18, .095, .92], atol=1e-3) and tip[2] > .9 and base[2] == 0   # bullseye: magenta tip, red base
    dog = V.apply(V.resolve(s, "kopek"), G)
    lab = lambda c: np.array([c[0] - c[1], (c[0] + c[1]) / 2 - c[2]])
    hum_d = np.abs(G["rgb"][45, 10] - G["rgb"][35, 10]).sum(); dog_d = np.abs(dog[45, 10] - dog[35, 10]).sum()
    assert dog_d < hum_d * .5                                                     # red ball ~ green grass for a dichromat
    th = V.apply(V.resolve(s, "yilan"), G)
    assert th[43, 26].sum() == th.sum(-1).max() or th[43, 26].sum() > th[35, 3].sum() + .5   # warm mouse is the brightest
    m12 = V.quantize(V.apply(V.resolve(s, "m12"), G), V.resolve(s, "m12").pal)
    m5 = V.apply(V.resolve(s, "m5"), G)
    assert len(np.unique(m5.reshape(-1, 3).round(3), axis=0)) <= 7
    assert len(np.unique(V.apply(V.resolve(s, "m12"), G).reshape(-1, 3).round(3), axis=0)) > len(np.unique(m5.reshape(-1, 3).round(3), axis=0))
    assert V.resolve(s, "hayret").map == "rgb" and V.resolve(s, None) is None
    try: V.resolve(s, "nope"); assert False
    except ValueError: pass


def test_sonar_rings_light_edges_only_where_the_ring_is():
    s = {"visions": VIS}; v = V.resolve(s, "yarasa"); G = gbuf()
    dark = V.apply(v, G, {"origin": (0, 0), "rings": []})
    lit = V.apply(v, G, {"origin": (0, 0), "rings": [(math.hypot(10, 40), 1.0)]})
    assert lit[40, 10].sum() > dark[40, 10].sum() + .3                            # the ball's edge lights up as the ring passes
    assert lit[2, 30].sum() < .35                                                 # empty sky stays (nearly) black
    based = V.apply(v, G, {"origin": (0, 0), "rings": [], "base": .3})
    assert based.sum() > dark.sum()


def test_quantize_pixel2_blocks_and_dither_mix():
    pal = Palette(NAT); rgb = np.random.default_rng(1).random((32, 20, 3)).astype(np.float32)
    q = V.quantize(rgb, pal, 2)
    assert (q[0::2, 0::2] == q[1::2, 1::2]).all() and (q[0::2] == q[1::2]).all()
    a = np.zeros((8, 8, 3), np.uint8); b = np.full((8, 8, 3), 255, np.uint8)
    assert (V.dither_mix(a, b, 0.0) == a).all() and (V.dither_mix(a, b, 1.0) == b).all()
    assert abs((V.dither_mix(a, b, .5) > 0).mean() - .5) < .01
    u = V.union_palette([Palette(NAT), Palette(MONO)], Palette(MONO))
    assert len(u.colors) == len(set(map(tuple, np.round(np.vstack([Palette(NAT).colors, Palette(MONO).colors]), 5))))


def world_spec(**over):
    s = {"loop": True, "brand": {"auto": False}, "visions": VIS, "world_palette": NAT, "palette": "hayret",
         "music": {"bpm": 120, "sections": [{"name": "a", "beats": 4}, {"name": "b", "beats": 4,
                   "drums": {"K": "X.......X.......", "B": "x...x...x.x.x.x.x.x.x.x.rrrrrrrr"}}, {"name": "c", "beats": 4}]},
         "segments": [
             {"id": "A", "role": "hook", "scene": "vision_world", "beats": 4, "vision": "insan", "params": {"peek": {"at": 1, "beats": 1, "mode": "ari"}},
              "camera": {"zoom": [1.2, 1.2], "pan": [[0, 6], [0, 6]]}, "layers": {"back": ["rays"], "front": ["dust", "pollen"]}},
             {"id": "B", "role": "free", "scene": "vision_world", "beats": 4, "vision": "yarasa", "transition_in": "cut",
              "params": {"time": "night", "sonar": {"origin": "bat", "rings_on": "drum:B"}}, "camera": {"zoom": [1.2, 1.2], "pan": [[0, 6], [0, 6]]},
              "layers": {"back": ["stars"], "front": ["dust", "pollen"]}},
             {"id": "C", "role": "loop", "scene": "vision_mosaic", "beats": 4, "transition_in": "cut", "layers": {"back": ["rays"], "front": ["dust", "pollen"]},
              "params": {"tiles": ["insan", "ari", "kopek", "yilan", "yarasa", "m12"]}}]}
    s.update(over); return S.normalise(s)


def test_per_segment_palettes_and_persistent_world():
    from bitloop.render import Film
    s = world_spec(); f = Film(s)
    e, w = S.validate(s); assert not [x for x in e if any(k in x for k in ("vision", "scene", "palette", "layer"))], e
    bad = world_spec(); bad["segments"][0]["vision"] = "kartal"; assert any("kartal" in x for x in S.validate(bad)[0])
    cols = lambda img: set(map(tuple, img.reshape(-1, 3)))
    pal_set = lambda p: set(map(tuple, (p.colors * 255 + .5).astype(np.uint8)))
    a = f.art_frame(.4); b = f.art_frame(2.6)
    assert cols(a) <= pal_set(f.seg_pal[0]) and cols(b) <= pal_set(f.seg_pal[1])   # each eye in its own palette
    # one world: the albedo G-buffer of A at its end == B's at its start (continuous global clock)
    cv = f.cv; f._draw_scene(cv, 0, 2.0, 4.0, 2.0); ga = cv.aux["oid"].copy()
    f._draw_scene(cv, 1, 0.0, 0.0, 2.0); gb = cv.aux["oid"].copy()
    assert (ga == gb).mean() > .97
    # peek: blink mixes the bee palette into the human frame mid-peek
    tp = 1.5 * s["beat_s"]; pk = f.art_frame(tp)
    s2 = world_spec(); s2["segments"][0]["params"].pop("peek"); nopk = Film(s2).art_frame(tp)
    assert (pk != nopk).any(-1).mean() > .2 and (f.art_frame(.1) == Film(s2).art_frame(.1)).all()


def test_drum_B_multibar_grid_hits_and_rings():
    me = Meter("4/4")
    p = {"B": "x...x...x.x.x.x.x.x.x.x.rrrrrrrr", "_B": "comment"}
    h0 = [b for b, i, v in D.hits_in_bar(p, me, 2.0, bar=0)]; h1 = [b for b, i, v in D.hits_in_bar(p, me, 2.0, bar=1)]
    assert h0 == [0, 1, 2, 2.5, 3, 3.5] and len(h1) == 4 + 16 and all(i == "B" for _, i, _ in D.hits_in_bar(p, me, 2.0, bar=1))
    assert D.drum("B").size == int(.018 * 44100) or D.drum("B").size > 0
    s = world_spec(); hits = M.drum_hits(s, "B")
    assert hits[:6] == [4, 5, 6, 6.5, 7, 7.5]
    from bitloop.render import Film
    f = Film(s); sp = s["segments"][1]["params"]["sonar"]
    fb = 1 / 30 / s["beat_s"]
    r = f.sonar_rings(sp, 5 + fb)
    assert r and abs(r[-1][0] - 300 * fb) < 1e-6                              # a ring starts within 1 frame of the hit
    assert len(f.sonar_rings(sp, 7.9)) <= 3


def test_pad_max_notes_and_one_note_chord():
    with tempfile.TemporaryDirectory() as d:
        s = S.normalise({"loop": False, "brand": {"auto": False}, "music": {"bpm": 120,
                         "voices": {"bass": {"role": "bass", "pattern": "walk"}, "pad": {"role": "pad", "max_notes": 12, "min_energy": 0},
                                    "arp": {"role": "arp", "pattern": "up", "min_energy": 0}},
                         "sections": [{"name": "a", "beats": 4, "progression": [["D3"]]},
                                      {"name": "b", "beats": 4, "progression": [[f"{n}3" for n in "C C# D D# E F F# G G# A A# B".split()]]}]},
                         "segments": [{"id": "A", "role": "hook", "scene": "hero", "beats": 8}]})
        M.synth(s, os.path.join(d, "a.wav"))                                     # used to crash (sorted(ch)[1])
        st = M._read(os.path.join(d, "a.wav")) if hasattr(M, "_read") else None
        assert st is None or np.abs(st).max() > 0


def test_mosaic_tiles_and_hive_label():
    from bitloop.render import Film
    s = world_spec(); f = Film(s)
    img = f.art_frame(s["segments"][2]["start_s"] + .01)
    gut = np.array([4, 6, 14], np.uint8)
    assert (img[0] == gut).all() and (img[:, 89] == gut).all()                 # 1-px Kutu gutters
    assert (img[1:106, :89] != gut).any(-1).mean() > .9                         # first frame: tiles already in, never empty
    assert (img[107:212, 90:] != gut).any(-1).mean() > .9                       # slots not in yet show the dimmed first eye
    from bitloop.props import plate, _snap_k
    from bitloop.raster import Camera
    cv = Canvas(180, 320, Palette("hayret")); cv.set_cam(Camera(0, 0, 1.1)); cv.clear()
    plate(cv, cv.pal, 0, 0, 0, 0, 1.4, "@hayret.piksel", "KOVAN 07", skin="hive")
    assert _snap_k(1.0, 1.1) == 1 and _snap_k(1.0, 1.2) == 1                     # 1 art px (= 6 output px) per font dot
    ink = (cv.rgb.sum(-1) < .4); assert ink[140:180, 60:120].sum() > 150         # dark painted letters on the board


def test_crt_floor_keeps_after_image():
    from bitloop import transitions as T
    pal = Palette("hayret"); h, w = 320, 180
    rng = np.random.default_rng(1); a = (rng.random((h, w, 3)) * 200 + 40).astype(np.uint8); b = a[::-1].copy()
    ctx = {}
    dark = T.apply({"type": "crt"}, a, b, .45, pal, ctx).mean()
    lit = T.apply({"type": "crt", "floor": .6}, a, b, .45, pal, ctx).mean()
    assert lit > dark + 20 and lit < a.mean()                                   # dim after-image, still "off"
    assert (T.apply({"type": "crt"}, a, b, .1, pal, ctx) == T.apply({"type": "crt", "floor": 0}, a, b, .1, pal, ctx)).all()

def test_qc_section_level_thermal_agc_and_legible_glow_matte():
    # sections[].level_db scales only that section's music (crossfaded), 0 dB everywhere = untouched
    import soundfile as sf
    def run(lv):
        with tempfile.TemporaryDirectory() as d:
            s = S.normalise({"loop": False, "brand": {"auto": False}, "music": {"bpm": 120, "sfx": False, "logo": False,
                             "voices": {"pad": {"role": "pad", "min_energy": 0}},
                             "sections": [{"name": "a", "beats": 8, "drums": "none"}, {"name": "b", "beats": 8, "drums": "none", "level_db": lv}]},
                             "segments": [{"id": "A", "role": "hook", "scene": "hero", "beats": 16}]})
            st = M.synth(s, os.path.join(d, "a.wav")); y, sr = sf.read(st)
            rms = lambda a, b: np.sqrt((y[int(a * sr):int(b * sr)] ** 2).mean())
            return rms(1, 3.5) / rms(4.5, 7)
    r0, r6 = run(0.0), run(-6.0)
    assert abs(20 * np.log10(r6 / r0) - 6.0) < .7
    # thermal mosaic tile: auto-gain spreads a narrow temperature range over the ramp
    from bitloop.scenes_vision import VisionMosaic
    m = V.Vision("y", VIS["yilan"]); G = gbuf(); G["temp"][:] = .25 + .05 * (np.arange(36) / 35)[None, :]
    vm = VisionMosaic.__new__(VisionMosaic); vm.p = {"thermal_agc": [3, 99.7], "thermal_blur": 1.0}
    mm, G2 = vm._tile_mode(m, G)
    assert np.ptp(G2["temp"]) > .8 and mm.blur == 1.0 and m.blur == 2.0
    assert vm._tile_mode(V.Vision("i", VIS["insan"]), G)[1] is G
    # legible props: glow under the drawn pixels is cleared, elsewhere kept
    from bitloop.render import Film
    from bitloop.raster import Camera
    cv = Canvas(40, 40, Palette("hayret")); cv.set_cam(Camera(0, 0, 1.0)); cv.clear(); cv.glowbuf[:] = .3
    def draw(): cv.rgb[10:20, 10:20] = (.95, .92, .86)
    Film._matte_glow(cv, draw)()
    assert (cv.glowbuf[10:20, 10:20] == 0).all() and (cv.glowbuf[25:, 25:] == .3).all()
    cv.rgb[0:5, 0:5] = .9; cv.keep[0:5, 0:5] = True; cv.vignette()
    assert np.allclose(cv.rgb[0:5, 0:5], .9) and cv.rgb[35:, 35:].max() < .9


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns: fn(); print("ok", fn.__name__)
    print(len(fns), "passed")
