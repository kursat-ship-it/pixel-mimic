"""chladni scene: particles settle on the nodal lines of a standing wave. Run: python tests/test_chladni.py"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from bitloop import spec as S
from bitloop.palette import Palette
from bitloop.scenes_chladni import Chladni


def mini(**p):
    lay = {"back": ["horizon", "nebula"], "front": ["dust"]}
    s = {"meta": {"lang": "tr"}, "loop": True,
         "music": {"bpm": 120, "meter": "4/4", "key": "A", "scale": "natural_minor", "flavour": "fm"},
         "segments": [
            {"id": "A", "role": "step", "beats": 20, "scene": "chladni", "params": p, "layers": lay,
             "caption": {"text": "SES GÖRÜNMEZ, KUM ELE VERİR?", "at": [0, 3]}},
            {"id": "B", "role": "reveal", "beats": 20, "scene": "chladni", "params": {"n": 4, "m": 4, "label": "mod 4,4"},
             "layers": lay, "transition_in": "cut"}]}
    return S.normalise(s)


def test_scene_registered_and_valid():
    s = mini(n=2, m=2, label="mod 2,2")
    e, w = S.validate(s)
    assert not e, e
    assert abs(s["duration_s"] - 20.0) < 1e-6


def test_nodal_lines_are_where_cos_is_zero():
    pal = Palette("hayret")
    sc = Chladni({"n": 2, "m": 1}, 1, pal, ".")
    u = np.array([0.0, 0.25, 0.5, 0.75, 1.0]); v = np.full_like(u, 0.4)
    tu, tv, d = sc._nodes(u, v)           # n=2 → vertical nodes at .25/.75 ; m=1 → horizontal at .5
    assert abs(tv[0] - 0.5) < 1e-9        # u=0 → nearest line is the horizontal .5
    assert abs(tu[1] - 0.25) < 1e-9 and abs(tv[1] - 0.4) < 1e-9   # u=.25 is a vertical node
    assert abs(tu[3] - 0.75) < 1e-9


def test_frame_renders_and_is_deterministic():
    from bitloop.render import Film
    spec = mini(n=3, m=2, label="mod 3,2")
    a = Film(spec).frame(2.0)
    b = Film(spec).frame(2.0)
    assert a.shape == (1920, 1080, 3) and a.dtype == np.uint8
    assert np.array_equal(a, b)
    assert not np.array_equal(Film(spec).frame(0.1), Film(spec).frame(2.0))   # sand settles over time


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v(); print("ok", k)
