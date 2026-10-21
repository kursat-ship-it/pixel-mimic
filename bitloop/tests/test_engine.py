"""Run: python tests/test_engine.py   (or python -m pytest tests)"""
import json, os, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from bitloop import spec as S
from bitloop.captions import upper, coverage, render, CaptionStyle
from bitloop.palette import Palette

T = os.path.join(os.path.dirname(__file__), "..", "bitloop", "templates")
REF = os.path.join(T, "reference_scale_journey.json")


def mini(loop=False, **music):
    s = {"meta": {"lang": "tr"}, "loop": loop, "music": music, "segments": [
        {"id": "A", "role": "hook", "beats": 4, "scene": "hero", "caption": {"text": "İŞĞÜÖÇ\nışık?", "at": [0, 3]}},
        {"id": "B", "role": "hit", "beats": 4, "scene": "network", "transition_in": "cut", "params": {"flare": True, "nodes": 40}}]}
    return S.normalise(s)


def test_reference_example_timing():
    s = S.load(REF); e, w = S.validate(s)
    assert any("unfilled template slots" in x for x in e)
    assert abs(s["total_beats"] - 94) < 1e-9 and abs(s["duration_s"] - 48.02) < .01 and s["palette"] == "violet-amber"


def test_defaults_brand_layer_constant_music_free():
    s = mini()
    assert s["format"]["fps"] == 30 and s["palette"] == "hayret" and s["brand"]["handle"] == "@hayret.piksel"
    assert s["music"]["logo"] and s["music"]["scale"] != "hicaz"            # Hicaz is an option, not the default
    h = mini(style="hicaz_maqsum"); assert h["music"]["scale"] == "hicaz" and h["music"]["drums"] == "maqsum"


def test_turkish_upper_and_glyphs():
    assert upper("istanbul ışık") == "İSTANBUL IŞIK"
    assert coverage("İŞĞÜÖÇ ışğüöç 0-9 +~%/?!") == [] and coverage("Ж") == ["Ж"]
    assert coverage("@hayret.piksel") == []


def test_caption_geometry_and_contrast():
    st = CaptionStyle(1080, 1920, Palette())
    a, x, y, dot = render("BİR\nİKİ\nÜÇ", st)
    assert dot == 12 and y == 186 and x % 6 == 0 and a.shape[1] <= 1080
    from bitloop.palette import contrast
    for c in ("#F4ECDC", "#41E8D2", "#FF9A86"): assert contrast(c, "#04060E") >= 7


def test_tempo_map_meters_and_ramps():
    from bitloop.timing import Meter, TempoMap
    assert Meter("7/8").bar_beats == 3.5 and Meter("7/8").grouping == [2, 2, 3] and Meter("6/8").bar_beats == 3
    assert Meter("9/8").group_starts == [0, 1, 2, 3]
    tm = TempoMap([(0, 8, 60, 60), (8, 16, 60, 120)], 16)
    assert abs(tm.time(8) - 8.0) < 1e-6 and abs(tm.time(16) - (8 + 8 * np.log(2))) < 1e-3   # ∫ 60/bpm(b) db
    for b in (0, 3.3, 8, 12.7, 16): assert abs(tm.beat(tm.time(b)) - b) < 1e-6
    s = S.normalise({"music": {"bpm": 90, "meter": "4/4", "sections": [{"bars": 2, "bpm_to": 150}, {"bars": 2, "meter": "7/8"}]},
                     "segments": [{"scene": "hero", "bars": 2}, {"scene": "hero", "bars": 2}]})
    assert s["total_beats"] == 8 + 7 and s["segments"][1]["start_beat"] == 8   # 2 bars of 7/8 = 7 beats


def test_scales_chords_makams():
    from bitloop.theory import SCALES, Scale, chord
    for n in SCALES:
        sc = Scale("D", n); assert len(chord("I", sc)) == 3 and len(chord("V7", sc)) == 4
    assert chord("Em", Scale("C", "major")) == [52.0, 55.0, 59.0] and chord(["E3", "G3"], Scale()) == [52.0, 55.0]
    u = Scale("D", "ussak", "approx"); assert abs(u.steps[1] - 1.5) < 1e-9          # segah 2nd ≈ 150 cents
    h = Scale("D", "hicaz"); assert h.steps[2] - h.steps[1] == 3                     # augmented 2nd


def test_frame_is_deterministic_and_on_palette():
    from bitloop.render import Film
    s = mini(); f1 = Film(s).frame(2.5); f2 = Film(s).frame(2.5)
    assert f1.shape == (1920, 1080, 3) and np.array_equal(f1, f2)
    pal = (Palette().colors * 255 + .5).astype(int)
    cols = np.unique(f1.reshape(-1, 3), axis=0)
    assert all((np.abs(pal - c).sum(1) <= 1).any() for c in cols)


def test_every_transition_is_palette_safe():
    from bitloop import transitions as TR
    from bitloop.render import Film
    s = mini(); f = Film(s); a = f._scene_img(f.cv, 0, 1.0); b = f._scene_img(f.cv2, 1, 3.0)
    pal = (f.pal.colors * 255 + .5).astype(int)
    for n in TR.TRANSITIONS:
        for k in (0.0, .37, .5, .81, 1.0):
            o = TR.apply(TR.normalise(n), a, b, k, f.pal, {"focus_a": (90, 160), "focus_b": (90, 160), "seed": 1, "mask": f._mask})
            assert o.shape == a.shape and o.dtype == np.uint8, n
            cols = np.unique(o.reshape(-1, 3), axis=0)
            assert all((np.abs(pal - c).sum(1) <= 1).any() for c in cols), n


def test_music_length_breath_and_hit_on_beat():
    from bitloop.music import synth, _read, SR
    s = mini(); d = tempfile.mkdtemp(); p = synth(s, os.path.join(d, "a.wav"))
    a = _read(p)[:, 0]; assert abs(len(a) / SR - s["duration_s"]) < 1e-3
    hit = int(s["segments"][1]["start_s"] * SR)
    pre = np.abs(a[hit - int(.2 * SR):hit - int(.02 * SR)]).mean(); post = np.abs(a[hit:hit + int(.1 * SR)]).mean()
    assert post > 3 * pre


def test_sync_holds_across_tempo_and_meter_changes():
    from bitloop.music import synth, _read, SR
    from bitloop.timing import tempo_map
    import scipy.signal as ss
    s = S.normalise({"music": {"bpm": 90, "drums": {"K": "X..............."}, "voices": {}, "logo": False, "sfx": False,
                               "sections": [{"bars": 2, "energy": 1, "bpm_to": 150}, {"bars": 2, "meter": "7/8", "energy": 1, "drums": {"K": "X............."}},
                                            {"bars": 2, "meter": "3/4", "energy": 1, "bpm_to": 80, "drums": {"K": "X..........."}}]},
                     "segments": [{"scene": "hero", "bars": 2}, {"scene": "hero", "bars": 2}, {"scene": "hero", "bars": 2}]})
    a = _read(synth(s, os.path.join(tempfile.mkdtemp(), "d.wav")))[:, 0]
    tm = tempo_map(s); bars = [0, 4, 8, 11.5, 15, 18]
    env = np.abs(a)
    for b in bars:
        t = tm.time(b); i = int(t * SR); w = env[max(0, i - 480):i + 960]
        onset = (np.argmax(w > .3 * w.max()) - (i - max(0, i - 480))) / SR
        assert abs(onset) < .005, (b, t, onset)                       # every downbeat within 5 ms


def test_sonic_logo_transposes_into_each_scale():
    from bitloop.theory import Scale
    def logo(sc): return [sc.degree(sc.fifth_index(), 4), sc.degree(0, 5), sc.degree(1, 5), sc.degree(2, 5)]
    hz = logo(Scale("D", "hicaz")); ly = logo(Scale("F", "lydian")); pt = logo(Scale("A", "pentatonic_minor"))
    assert hz[3] - hz[2] == 3 and ly[1] % 12 == 5 and pt[1] % 12 == 9 and len({tuple(hz), tuple(ly), tuple(pt)}) == 3


def test_every_scene_has_three_moving_layers():
    from bitloop.render import Film
    for back, front in Film(mini()).stacks: assert len(back) + len(front) >= 3


def test_archetypes_and_blank_only_miss_their_slots():
    from bitloop.archetypes import ARCHETYPES, make
    specs = [make(n) for n in ARCHETYPES] + [json.load(open(os.path.join(T, "blank.json"), encoding="utf-8"))]
    for sp in specs:
        s = S.normalise(sp); e, w = S.validate(s)
        assert all("unfilled template slots" in x for x in e), (sp.get("_archetype"), e)
        assert 20 <= s["duration_s"] <= 45, s["duration_s"]
        txt, R = S.retention_map(s); assert "HOOK" in txt and "LOOP" in txt and "TAG" in txt


def test_validator_retention_and_brand_rules():
    s = S.normalise({"loop": False, "brand": {"auto": False}, "segments": [
        {"scene": "hero", "beats": 40, "role": "hook", "caption": {"text": "@hayret.piksel", "at": [6, 9]}}]})
    e, w = S.validate(s)
    assert any("handle may not appear" in x for x in e) and any("legibly" in x for x in e)
    assert any("no hook caption in the first 2 s" in x for x in e) and any("static stretch" in x for x in w)


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"): v(); print("ok", k)
