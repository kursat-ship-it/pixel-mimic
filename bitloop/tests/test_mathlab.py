"""formula_scope (neon XY oscilloscope from the brief's functions) + neon palette. Run: python tests/test_mathlab.py"""
import os, sys, math
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from bitloop import spec as S
from bitloop.palette import Palette
from bitloop.scenes_mathlab import FormulaScope, FORMULA


def mini(**p):
    lay = {"back": ["grid", "nebula"], "front": ["dust"]}
    s = {"meta": {"lang": "tr"}, "loop": True, "pacing": "punchy",
         "music": {"bpm": 120, "meter": "4/4", "key": "F", "scale": "phrygian_dominant", "flavour": "sid"},
         "segments": [
            {"id": "A", "role": "step", "beats": 20, "scene": "formula_scope", "params": p, "layers": lay,
             "caption": {"text": "99 DEĞİL, 9 FONKSİYON?", "at": [0, 3]}},
            {"id": "B", "role": "reveal", "beats": 20, "scene": "formula_scope", "params": {"formula": "all"},
             "layers": lay, "transition_in": "cut"}]}
    return S.normalise(s)


def test_scene_registered_and_valid():
    s = mini(formula="hardtekk", formula_text="y = mod(8t,1) > 0.9 ? 1 : -1")
    e, w = S.validate(s)
    assert not e, e
    assert abs(s["duration_s"] - 20.0) < 1e-6


def test_curves_are_exact():
    pal = Palette("hayret")
    hard = FormulaScope({"formula": "hardtekk"}, 1, pal, ".")
    assert hard._f(FORMULA["hardtekk"], 0.0) == -1.0
    assert hard._f(FORMULA["hardtekk"], 0.12) == 1.0          # 8·0.12 = 0.96 → mod > 0.9
    eight08 = FormulaScope({"formula": "phonk808"}, 1, pal, ".")
    assert abs(eight08._f(FORMULA["phonk808"], 0.0)) < 1e-9   # sin(0)·… = 0
    funk = FormulaScope({"formula": "funk"}, 1, pal, ".")
    assert abs(funk._f(FORMULA["funk"], 0.0) - 0.5 * math.sin(math.pi / 4)) < 1e-9


def test_frame_renders_and_is_deterministic():
    from bitloop.render import Film
    spec = mini(formula="build", formula_text="y = sin(2π·(100+50t)·t)\n·(t/3)")
    a = Film(spec).frame(2.0)
    b = Film(spec).frame(2.0)
    assert a.shape == (1920, 1080, 3) and a.dtype == np.uint8
    assert np.array_equal(a, b)


def test_all_mode_renders():
    from bitloop.render import Film
    spec = mini(formula="all")
    fr = Film(spec).frame(16.0)
    assert fr.shape == (1920, 1080, 3) and fr.dtype == np.uint8


def test_neon_palette_has_brand_colours():
    from palettes import PALETTES
    pal = Palette(PALETTES["neon"])
    assert pal.ramps["energy"].shape[0] >= 3
    assert "#FF00FF" in [c for c in PALETTES["neon"]["colors"]]


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v(); print("ok", k)
