"""pendulum_grid scene (99 Kuramoto-coupled pendulums), Σ/φ glyphs, tick_hi SFX. Run: python tests/test_sync.py"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from bitloop import spec as S, sfx as SFX
from bitloop.palette import Palette
from bitloop.scenes_sync import PendulumGrid


def mini(**p):
    lay = {"back": ["stars", "nebula"], "front": ["dust"]}
    s = {"meta": {"lang": "tr"}, "loop": True,
         "music": {"bpm": 120, "meter": "4/4", "key": "A", "scale": "dorian", "flavour": "fm"},
         "segments": [
            {"id": "A", "role": "hook", "beats": 16, "scene": "pendulum_grid", "params": p, "layers": lay,
             "caption": {"text": "99 SARKAÇ", "at": [0, 3]}},
            {"id": "B", "role": "reveal", "beats": 16, "scene": "pendulum_grid", "params": p, "layers": lay,
             "transition_in": "dissolve",
             "props": [{"kind": "plate", "x": 0, "y": 72, "s": 1.4, "model": "SARKAÇ 99", "layer": "front", "par": 1.0,
                        "from": 2, "legible": True}]}]}
    return S.normalise(s)


def test_scene_registered_and_valid():
    s = mini()
    e, w = S.validate(s)
    assert not e, e
    assert abs(s["duration_s"] - 16.0) < 1e-6
    assert s["segments"][0]["scene"] == "pendulum_grid"


def test_frame_renders_and_is_deterministic():
    from bitloop.render import Film
    spec = mini()
    a = Film(spec).frame(1.0)
    b = Film(spec).frame(1.0)
    assert a.shape == (1920, 1080, 3) and a.dtype == np.uint8
    assert np.array_equal(a, b), "frames must be a pure function of t (seeded, deterministic)"
    # the reveal frame (ring + formula active, t≈14.5 s) differs from the hook frame (chaos)
    assert not np.array_equal(Film(spec).frame(1.0), Film(spec).frame(14.5))


def test_phase_shared_across_segment_instances():
    """Different segment instances (different seeds) must share one world, or the cut would jump."""
    pal = Palette("hayret")
    a = PendulumGrid({}, 1000, pal, "."); a.b0 = 0.0
    b = PendulumGrid({}, 5555, pal, "."); b.b0 = 12.0
    for gb in (0.0, 3.0, 7.5, 15.0, 24.0, 29.5):
        for j in (0, 7, 49, 98):
            assert abs(a._phase(gb, j) - b._phase(gb, j)) < 1e-9, (gb, j)
    # the outlier (49) never locks: at the end its phase is measurably off the group
    assert abs(a._phase(24.0, 49) - a._phase(24.0, 0)) > 0.05


def test_sigma_phi_glyphs():
    from bitloop.pixfont import missing
    assert missing("Σφ|") == [], missing("Σφ|")
    assert "👀" in missing("👀")              # emoji still absent from the pixel font


def test_tick_hi_sfx():
    a = SFX.render("tick", 60, 0.5)
    b = SFX.render("tick_hi", 60, 0.5)
    assert a and b and len(a) == len(b) == 1
    assert len(a[0][1]) == len(b[0][1])                     # same duration/envelope
    assert not np.array_equal(a[0][1], b[0][1])             # different pitch


def test_sfx_ticks_deterministic():
    pal = Palette("hayret")
    sc = PendulumGrid({}, 1000, pal, "."); sc.b0 = 0.0
    ticks = sc.sfx(30.0)
    assert ticks and all(0.0 <= b < 30.0 and k in ("tick", "tick_hi") for b, k in ticks)
    assert any(k == "tick_hi" for _, k in ticks)            # the outlier is audible
    assert ticks == sc.sfx(30.0)                            # deterministic


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v(); print("ok", k)
