"""Series voices, Shepard riser and the fractal/music scene pack.  Run: python tests/test_fractal.py"""
import os, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from bitloop import spec as S
from bitloop.palette import Palette


def _series_spec(riser_kind="noise", loop=True):
    V = {"lead": {"role": "lead", "type": "pulse", "octave": 5, "series": {"name": "norgard", "rate": 4}},
         "counter": {"role": "counter", "type": "pulse", "octave": 4, "series": {"name": "norgard", "rate": 2, "sign": -1}},
         "lead_q": {"role": "lead", "type": "pulse", "octave": 5, "series": {"name": "norgard", "rate": 1}},
         "bass": {"role": "bass", "type": "triangle", "octave": 3, "series": {"name": "norgard", "rate": 1}}}
    return S.normalise({"loop": loop, "music": {"bpm": 100, "key": "G", "scale": "dorian", "voices": V, "logo": False, "sections": [
        {"beats": 8, "energy": 2, "voices": ["lead", "counter", "bass"]},
        {"beats": 8, "energy": 1.5, "riser": True, "riser_kind": riser_kind, "stop": .5, "voices": ["counter"]},
        {"beats": 8, "energy": 3, "scale": "lydian", "voices": ["lead", "lead_q", "bass"]}]},
        "segments": [{"scene": "fractal_staff", "beats": 8, "role": "hook", "caption": {"text": "BU MELODİ", "at": [0, 3]}},
                     {"scene": "shepard_stairs", "beats": 8}, {"scene": "mandel_zoom", "beats": 8}]})


def _notes(s):
    from bitloop.music import series_notes, _voices, _active, logo_windows
    from bitloop.theory import Scale
    V = _voices(s); out = {}
    for sec in s["_sections"]:
        sc = Scale(sec["key"], sec["scale"])
        for n in _active(sec, V):
            if V[n].get("series"):
                for b, d, m, vk in series_notes(V[n], sec, sc, logo_win=logo_windows(s)):
                    out.setdefault(n, {})[round(b, 4)] = m
    return out


def test_norgard_series_and_self_similarity():
    from bitloop.theory import norgard, series_index
    a = [int(norgard(i)) for i in range(16)]
    assert a[:8] == [0, 1, -1, 2, 1, 0, -2, 3]
    n = np.arange(1, 400)
    assert np.array_equal(norgard(2 * n), -norgard(n)) and np.array_equal(norgard(4 * n), norgard(n))
    assert np.array_equal(norgard(2 * n + 1), norgard(n) + 1)
    assert series_index(2.75, 4) == 11 and series_index(2.75, 1) == 2 and series_index(9.0, 4, period=32) == 4


def test_slow_voices_are_every_2nd_and_4th_lead_note():
    s = _series_spec(); N = _notes(s); L = N["lead"]
    shared = 0
    for name, step in (("counter", .5), ("lead_q", 1.0), ("bass", 1.0)):
        for b, m in N.get(name, {}).items():
            assert abs(b / step - round(b / step)) < 1e-6, (name, b)       # on its own grid
            if b in L:
                shared += 1
                d = (L[b] - m) % 12
                assert d == 0, (name, b, L[b], m)                           # same pitch class as the lead note there
    assert shared >= 12
    # lead_q is literally the lead at quarter-notes: same register, same MIDI note
    for b, m in N["lead_q"].items():
        if b in L: assert L[b] == m


def test_series_respects_section_scale():
    from bitloop.theory import Scale
    s = _series_spec(); N = _notes(s)
    ly = {(7 + k) % 12 for k in (0, 2, 4, 6, 7, 9, 11)}; do = {(7 + k) % 12 for k in (0, 2, 3, 5, 7, 9, 10)}
    for b, m in N["lead"].items():
        assert m % 12 in (ly if b >= 16 else do), (b, m)
    assert any(m % 12 == 1 for b, m in N["lead"].items() if b >= 16)        # the lydian #4 (C#) actually sounds


def test_shepard_riser_rises_and_validates():
    from bitloop.music import synth, _read, SR
    s = _series_spec("shepard"); e, w = S.validate(s)
    assert not [x for x in e if "riser" in x or "series" in x], e
    a = _read(synth(s, os.path.join(tempfile.mkdtemp(), "sh.wav")))[:, 0]
    t0, t1 = s["_sections"][1]["b0"] * .6, (s["_sections"][1]["b1"] - .5) * .6
    seg = a[int(t0 * SR):int(t1 * SR)]
    q = len(seg) // 4; rms = [np.sqrt((seg[i * q:(i + 1) * q] ** 2).mean()) for i in range(4)]
    assert rms[3] > rms[0] * 1.5, rms                                      # crescendo
    stop = a[int(t1 * SR) + 400:int(t1 * SR) + int(.25 * SR)]
    assert np.abs(stop).max() < np.abs(seg).max()                          # the held breath really is quieter
    bad = S.normalise({"music": {"sections": [{"beats": 4, "riser_kind": "laser"}]}, "segments": [{"scene": "hero", "beats": 4}]})
    assert any("riser_kind" in x for x in S.validate(bad)[0])


def test_new_scenes_render_on_palette_and_move():
    from bitloop.render import Film
    s = _series_spec(); f = Film(s)
    pal = (Palette().colors * 255 + .5).astype(int)
    for t in (1.0, 6.0, 11.0):
        a, b = f.frame(t), f.frame(t + .4)
        cols = np.unique(a[::4, ::4].reshape(-1, 3), axis=0)
        assert all((np.abs(pal - c).sum(1) <= 1).any() for c in cols), t
        assert (a != b).mean() > .02, t                                    # something moves
    for back, front in f.stacks: assert len(back) + len(front) >= 3


def test_every_new_scene_draws_something():
    from bitloop.scenes import SCENES
    from bitloop.raster import Canvas, Camera
    pal = Palette()
    for name in ("fractal_staff", "koch", "noise_scope", "series_tree", "shepard_stairs", "mandel_zoom"):
        sc = SCENES[name]({}, 3, pal).bind({"start_beat": 0, "end_beat": 8}, {"total_beats": 8, "loop": True})
        cv = Canvas(180, 320, pal); cv.set_cam(Camera(0, 0, 1, 0)); cv.clear(); empty = cv.composite().copy()
        sc.draw(cv, 2.4, 4.0, 8); img = cv.composite()
        assert (img != empty).any(axis=2).mean() > .03, name


def test_vinyl_is_a_legible_object():
    assert "vinyl" in S.LEGIBLE_OBJECTS
    s = S.normalise({"segments": [{"scene": "object", "beats": 8, "role": "reveal",
                                   "params": {"kind": "vinyl", "brand": "@hayret.piksel", "brand_at": 0, "label_text": "SONSUZ PLAK"}}]})
    e, w = S.validate(s); assert not [x for x in e if "legib" in x], e
    from bitloop.render import Film
    img = Film(s).frame(3.0); pal = Palette()
    cream = (pal.ramp("pale", 1.0) * 255).astype(int)
    assert (np.abs(img.astype(int) - cream).sum(2) < 40).mean() > .01      # the cream label is there


def test_koch_and_mandel_math():
    from bitloop.scenes_math import koch_points, mandel
    for L in range(4):
        pts, new = koch_points(L, 1.0, 50, 0, 0, 0); assert len(pts) == 3 * 4 ** L and len(new) == (3 * 4 ** (L - 1) if L else 0)
    half, _ = koch_points(2, .5, 50, 0, 0, 0); full, _ = koch_points(2, 1.0, 50, 0, 0, 0)
    assert np.abs(np.array(half) - np.array(full)).max() > 1                  # growth animates the newest bumps
    mu = mandel(np.array([-1.0, 0.0, -.1 + .8j, 2.0]) + 0j, 64)
    assert np.isnan(mu[0]) and np.isnan(mu[1]) and np.isfinite(mu[3]) and mu[3] < 3   # -1, 0 inside; 2 escapes fast


def test_loop_seam_layer_sync_frame_identity():
    from bitloop.render import Film
    s = S.normalise({"loop": True, "segments": [
        {"scene": "fractal_staff", "beats": 4, "role": "hook"},       # (a caption popping in at frame 0 is the creator's call)
        {"scene": "koch", "beats": 4},
        {"scene": "fractal_staff", "beats": 4, "layer_sync": "first", "params": {"converge_to_frame0": True}}]})
    f = Film(s); T = s["duration_s"]; dt = 1 / 30
    diff = lambda x, y: (np.abs(x.astype(int) - y.astype(int)).sum(2) > 30).mean()
    a0, a1, z = f.frame(0.0), f.frame(dt), f.frame(T - dt)
    assert diff(z, a0) <= 1.5 * diff(a0, a1) + .005, (diff(z, a0), diff(a0, a1))   # the seam is just another frame step


def test_spin_over_has_no_black_gap_and_is_palette_safe():
    from bitloop import transitions as TR
    from bitloop.render import Film
    s = _series_spec(); f = Film(s); a = f._scene_img(f.cv, 0, 1.0); b = f._scene_img(f.cv2, 1, 3.0)
    pal = (f.pal.colors * 255 + .5).astype(int); bg = pal[0]
    for k in (0.0, .3, .5, .7, .95):
        o = TR.apply(TR.normalise({"type": "spin", "over": True}), a, b, k, f.pal, {"focus_a": (90, 160), "focus_b": (90, 160), "seed": 1, "mask": f._mask})
        assert (np.abs(o.astype(int) - bg).sum(2) == 0).mean() < .6, k
        cols = np.unique(o.reshape(-1, 3), axis=0); assert all((np.abs(pal - c).sum(1) <= 1).any() for c in cols)


def test_validator_rejects_bad_series():
    s = S.normalise({"music": {"voices": {"lead": {"role": "lead", "series": {"name": "fibonacci", "rate": 99}}},
                               "sections": [{"beats": 4, "voices": ["lead"]}]}, "segments": [{"scene": "hero", "beats": 4}]})
    e, w = S.validate(s); assert any("series" in x for x in e), e


def test_snapped_text_pixel_exact_and_portal_no_black_frame():
    """QC fixes: snapped in-world text keeps every glyph column at any zoom < 1.75 px/dot;
    portal no longer bitmap-scales the frames (no bg-filled black border)."""
    from bitloop.raster import Canvas, Camera
    from bitloop.bitmap import Bitmap, draw_bitmap
    from bitloop import transitions as TR
    s = _series_spec(); from bitloop.render import Film; f = Film(s); pal = f.pal
    arr = np.zeros((7, 5), bool); arr[:, ::2] = True                      # 3 one-dot columns
    for z in (1.0, 1.07, 1.3, 1.47):
        cv = Canvas(180, 320, pal); cv.set_cam(Camera(0.3, -0.2, z, 0.0)); cv.rgb[:] = 0
        draw_bitmap(cv, Bitmap(arr, 0, 0, 1.0), (1, 1, 1), 1.0, snap=True)
        cols = np.nonzero(cv.rgb[..., 0].max(0) > .5)[0]
        assert len(cols) == 3 * max(1, round(z)), (z, cols)
    a = np.full((320, 180, 3), 40, np.uint8); b = np.full((320, 180, 3), 200, np.uint8)
    o = TR.apply(TR.normalise("portal"), a, b, .98, pal, {"focus_a": (90, 160), "focus_b": (90, 160), "seed": 0})
    assert (o == 0).all(2).mean() == 0                                     # no bg-filled border from a shrunk copy


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"): v(); print("ok", k)
