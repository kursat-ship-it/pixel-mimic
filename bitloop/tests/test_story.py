"""Story pack: list series (series_defs), lookahead voices, section gain, sprites, the five story scenes and the
book object.  Run: python tests/test_story.py   (or python -m pytest tests)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from bitloop import spec as S
from bitloop.palette import Palette

MEL = [0, 2, 4, 2, 0, 4, 7, 4, 5, 4, 2, 4, 1, -1, -1, 0]


def _spec(lookahead=1, gain=None, loop=True):
    V = {"lead": {"role": "lead", "type": "pulse", "octave": 5, "series": {"name": "mel", "rate": 2}},
         "ahead": {"role": "counter", "type": "pulse", "octave": 6, "series": {"name": "mel", "rate": 2, "lookahead": lookahead}}}
    sec = {"beats": 8, "energy": 2, "voices": ["lead", "ahead"]}
    if gain: sec["gain"] = gain
    return S.normalise({"loop": loop, "music": {"bpm": 120, "key": "E", "scale": "minor", "logo": False, "voices": V,
                                                "series_defs": {"mel": {"values": MEL, "period": 16}}, "sections": [sec]},
                        "segments": [{"scene": "future_book", "beats": 8, "role": "hook"}]})


def _notes(s, name):
    from bitloop.music import series_notes, _voices
    from bitloop.theory import Scale
    V = _voices(s); sec = s["_sections"][0]; sc = Scale(sec["key"], sec["scale"])
    return series_notes(V[name], sec, sc)


def test_series_defs_register_and_do_not_leak():
    from bitloop.theory import series_value, SERIES
    _spec()
    assert [int(series_value("mel", i)) for i in range(18)] == MEL + MEL[:2]
    assert np.array_equal(series_value("mel", np.arange(16)), np.array(MEL))
    S.normalise({"segments": [{"scene": "hero", "beats": 4}]})                 # another spec: list series are dropped
    assert "mel" not in SERIES and "norgard" in SERIES


def test_validator_series_defs_and_lookahead():
    bad = S.normalise({"music": {"series_defs": {"x": {"values": [0, 1.5]}, "norgard": [0, 1]},
                                 "voices": {"l": {"role": "lead", "series": {"name": "norgard", "rate": 2, "lookahead": -3}}},
                                 "sections": [{"beats": 4, "voices": ["l"]}]}, "segments": [{"scene": "hero", "beats": 4}]})
    e, _ = S.validate(bad)
    assert any("series_defs" in x for x in e) and any("lookahead" in x for x in e), e
    e, _ = S.validate(_spec()); assert not [x for x in e if "series" in x or "lookahead" in x], e


def test_lookahead_voice_plays_the_next_note():
    s = _spec(lookahead=1)
    L = {round(b, 4): m for b, d, m, vk in _notes(s, "lead")}
    A = {round(b, 4): m for b, d, m, vk in _notes(s, "ahead")}
    assert len(L) == 16 and set(L) == set(A)
    for b in sorted(L)[:-1]:
        assert (A[b] - L[round(b + .5, 4)]) % 12 == 0, b                      # slot n = the lead's slot n+1


def test_section_gain_trims_one_voice():
    v0 = [vk for *_, vk in _notes(_spec(), "ahead")]
    v1 = [vk for *_, vk in _notes(_spec(gain={"ahead": .5}), "ahead")]
    l1 = [vk for *_, vk in _notes(_spec(gain={"ahead": .5}), "lead")]
    l0 = [vk for *_, vk in _notes(_spec(), "lead")]
    assert np.allclose(np.array(v1), .5 * np.array(v0)) and np.allclose(l0, l1)


def test_hero_sprites_well_formed():
    from bitloop.sprites import HERO, ROLES, hero_frame
    need = {"front", "blink", "look_l", "look_r", "read", "wow", "walk1", "walk2", "walk3", "turn"}
    assert need <= set(HERO)
    for k, rows in HERO.items():
        assert len(rows) == 22 and all(len(r) == 16 for r in rows), k
        assert set("".join(rows)) <= set(ROLES) | {"."}, k
        assert all(ch == "." for ch in rows[0][:4] + rows[0][-4:]), k            # head silhouette, not a block
        assert any(c != "." for c in rows[-1]), k                                # feet on the bottom row
    assert len({tuple(hero_frame("walk", b)) for b in np.arange(0, 1, .25)}) == 3  # 3-frame walk cycle
    assert sum(r.count("e") for r in HERO["front"]) == 4                         # two 1×2 eyes


STORY = [("future_book", {"mode": "read"}), ("future_book", {"mode": "avoid", "actual_series": "mel"}),
         ("future_book", {"mode": "open"}), ("laplace_demon", {}), ("dominoes", {}), ("dominoes", {"split": True}),
         ("libet_clock", {}), ("future_tree", {"mode": "dice"}), ("future_tree", {"mode": "burst"})]


def _draw(name, params, lb, zoom=1.0, total=8):
    from bitloop.scenes import SCENES
    from bitloop.raster import Canvas, Camera
    pal = Palette()
    sc = SCENES[name](params, 3, pal).bind({"start_beat": 0, "end_beat": 8}, {"total_beats": total, "loop": True})
    cv = Canvas(180, 320, pal); cv.set_cam(Camera(0, 0, zoom, 0)); cv.clear(); empty = cv.composite().copy()
    sc.draw(cv, lb * .5, lb, 8)
    return cv.composite(), empty, pal, sc


def test_story_scenes_populated_at_frame0_with_lower_third_and_on_palette():
    _spec()                                                                       # registers 'mel'
    for name, prm in STORY:
        z = 2.2 if prm.get("mode") == "burst" else 1.0                            # burst opens zoomed in (pull-out)
        img, empty, pal, _ = _draw(name, dict(prm, roll_series="mel") if name == "future_book" else prm, 0.0, zoom=z)
        ch = (img != empty).any(axis=2)
        assert ch.mean() > .05, (name, prm, ch.mean())                            # no near-empty first frame
        assert ch[214:].mean() > .04, (name, prm, ch[214:].mean())               # lower third is filled
        P = (pal.colors * 255 + .5).astype(int)
        cols = np.unique(img[::3, ::3].reshape(-1, 3), axis=0)
        assert all((np.abs(P - c).sum(1) <= 1).any() for c in cols), (name, prm)


def test_story_scenes_move_and_are_deterministic():
    _spec()
    for name, prm in STORY:
        prm = dict(prm, roll_series="mel") if name == "future_book" else prm
        a, _, _, _ = _draw(name, prm, 2.0); b, _, _, _ = _draw(name, prm, 2.6); a2, _, _, _ = _draw(name, prm, 2.0)
        assert (a != b).any(axis=2).mean() > .005, (name, prm)
        assert np.array_equal(a, a2), (name, prm)


def test_scene_specific_mechanics():
    from bitloop.scenes_story import accumulator_epochs, DIE_FACES, Dominoes
    u, ep = accumulator_epochs(n_epochs=60, leak=2.4, seed=3)
    avg = ep.mean(0); i0 = np.argmin(np.abs(u)); im = np.argmin(np.abs(u + 1.5))
    assert abs(avg[i0] - 1) < .1 and abs(avg[im]) < .3 and avg[i0 - 40] < avg[i0 - 10] < avg[i0]   # averaged noise → ramp
    assert all(DIE_FACES[n] + DIE_FACES[tuple(-x for x in n)] == 7 for n in DIE_FACES)
    d = Dominoes({}, 1, Palette()).bind({"start_beat": 0, "end_beat": 8}, {"total_beats": 8})
    assert sum(d._fallen(i, 0.0) >= 1 for i in range(24)) == 4                # pre-rolled: 4 already down
    assert all(abs(b * 4 - round(b * 4)) < 1e-9 for b, k in d.sfx(8))           # ticks on the 16th grid


def test_book_is_a_legible_object_and_closes():
    assert "book" in S.LEGIBLE_OBJECTS
    s = S.normalise({"segments": [{"scene": "object", "beats": 8, "role": "reveal",
                                   "params": {"kind": "book", "brand": "@hayret.piksel", "brand_at": 1.0, "close_at": .5}}]})
    e, w = S.validate(s); assert not [x for x in e if "legib" in x], e
    from bitloop.render import Film
    from bitloop.scenes import SCENES
    f = Film(s)
    assert (.5, "thud") in f.scenes[0].sfx(8)
    open_, closed = f.frame(0.0), f.frame(3.0)
    tq = np.array([0x41, 0xE8, 0xD2])                                    # Türkuaz Işık
    near = lambda img, c: (np.abs(img.astype(int) - c).sum(2) < 60)
    assert near(open_, tq).mean() > .01                                          # big türkuaz arrow on the open page
    # publisher line: türkuaz on the dark matte plate in the cover's lower part
    assert near(closed[1060:1400, 200:880], tq).mean() > .03
    assert (open_ != closed).any(axis=2).mean() > .2


def test_story_seam_converges():
    from bitloop.render import Film
    _spec()
    s = S.normalise({"loop": True, "music": {"series_defs": {"mel": MEL}}, "segments": [
        {"scene": "future_book", "beats": 4, "role": "hook", "params": {"roll_series": "mel"}},
        {"scene": "dominoes", "beats": 4},
        {"scene": "future_book", "beats": 4, "layer_sync": "first", "params": {"mode": "open", "roll_series": "mel"}}]})
    f = Film(s); T = s["duration_s"]; dt = 1 / 30
    diff = lambda x, y: (np.abs(x.astype(int) - y.astype(int)).sum(2) > 30).mean()
    a0, z = f.frame(0.0), f.frame(T - dt)
    spb = 60 / s["music"]["bpm"]
    step = max(diff(f.frame(k * spb - dt), f.frame(k * spb)) for k in (1, 2, 3))   # ordinary on-beat frame steps
    assert diff(z, a0) <= 1.25 * step + .005, (diff(z, a0), step)               # the seam is just another beat


if __name__ == "__main__":
    for k, fn in list(globals().items()):
        if k.startswith("test_"): fn(); print("ok", k)
