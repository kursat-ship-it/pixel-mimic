"""Cosmos pack (evren-anlamak): --package cover_t, superscript/Greek pixfont + formula bitmaps, minifont comma, seeded
"random" arp + unknown-pattern warning, kid sprite, scene-painted brand tags, own_layers, cosmic_zoom (rigid nesting,
rewind ends on frame 0), chalk_unify (one persistent board), galaxy_chess (CA synced to the music series),
laplace chaos twins (split exactly at diverge_at), bt709 tags in the encoder.
Run: python tests/test_cosmos.py   (or python -m pytest tests)"""
import inspect, math, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from bitloop import spec as S
from bitloop.palette import Palette


def test_cover_t_reads_meta():
    from bitloop.cli import cover_t
    assert cover_t({"meta": {"cover_t": 32.4}, "duration_s": 48.0}) == 32.4
    assert cover_t({"cover_t": 3.0, "duration_s": 48.0}) == 3.0          # legacy top-level key still works
    assert cover_t({"meta": {}, "duration_s": 48.0}) == 1.0
    assert cover_t({"meta": {"cover_t": 99}, "duration_s": 10.0}) < 10.0  # clamped inside the film


def test_superscripts_and_greek():
    from bitloop.pixfont import missing, SUPERSCRIPT, line_bitmap
    assert missing("Gμν=8πGTμν iħ∂ψ/∂t=Ĥψ 10¹²⁰ ρλΛ") == []
    assert "10" + "120".translate(SUPERSCRIPT) == "10¹²⁰"
    b = line_bitmap([("¹²⁰", False)])[0]
    rows = np.nonzero(b.any(1))[0]
    assert rows.max() <= 5, rows            # superscripts sit high in the 10-row cell
    d = line_bitmap([("1", False)])[0]; assert np.nonzero(d.any(1))[0].max() > rows.max()


def test_formula_bitmap_subscripts_hang_below():
    from bitloop.bitmap import formula_bitmap
    a = formula_bitmap("G_{μν}"); g = formula_bitmap("G")
    assert a.shape[0] > g.shape[0] and a.shape[1] > g.shape[1]
    sub_cols = a[:, g.shape[1] + 1:]
    assert np.nonzero(sub_cols.any(1))[0].max() >= g.shape[0] - 1      # the subscript reaches the baseline and below
    e = formula_bitmap("E = mc^{2}"); assert e.any()
    a1 = formula_bitmap("G_{μν}", scale=1); g1 = formula_bitmap("G", scale=1)        # 1 art px per dot: minifont scripts
    assert a1.shape[0] > g1.shape[0] and a1[g1.shape[0]:, g1.shape[1]:].any()        # hangs below the baseline


def test_minifont_comma():
    from bitloop.minifont import GLYPHS, mini_bitmap
    assert "," in GLYPHS and GLYPHS[","][6].any()
    assert mini_bitmap("FARK 0,0001").shape[1] > 0


def _music_spec(pattern):
    return S.normalise({"loop": True, "music": {"bpm": 120, "key": "E", "scale": "minor", "seed": 7, "logo": False,
                        "voices": {"arp": {"role": "arp", "type": "pulse", "octave": 5, "pattern": pattern, "rate": 4}},
                        "sections": [{"beats": 8, "energy": 2, "voices": ["arp"]}]},
                        "segments": [{"scene": "void", "beats": 8, "role": "hook"}]})


def _arp_notes(s):
    import tempfile
    from bitloop import music as M
    rec = []; orig = M.vnote
    def spy(v, midi, *a, **k):
        if v.get("pattern") == "random": rec.append(midi)
        return orig(v, midi, *a, **k)
    M.vnote = spy
    try: M.synth(s, os.path.join(tempfile.mkdtemp(), "a.wav"))
    finally: M.vnote = orig
    return rec


def test_random_arp_is_seeded_and_never_repeats():
    a = _arp_notes(_music_spec("random")); b = _arp_notes(_music_spec("random"))
    assert len(a) >= 16 and a == b                                  # seeded: identical renders
    assert all(x != y for x, y in zip(a, a[1:]))                    # never the same tone twice in a row
    assert len(set(a)) >= 3 and a != sorted(a)                      # not an up-run


def test_unknown_pattern_warns():
    errs, warns = S.validate(_music_spec("zigzag"))
    assert any("zigzag" in w for w in warns), warns


def test_kid_sprite_frames():
    from bitloop.sprites_kid import KID, KID_ROLES
    for name in ("front", "up", "q", "front_blink", "wow", "up_blink"):
        rows = KID[name]; assert len(rows) == 24 and all(len(r) == 20 for r in rows), name
        assert set("".join(rows)) - {"."} <= set(KID_ROLES), name


def test_snap_colour_returns_palette_entry():
    from bitloop.sprites import snap_colour
    p = Palette(S.normalise({"segments": [{"scene": "void", "beats": 4}]})["palette"])
    c = snap_colour(p, np.array([1.0, 0.0, 0.0], np.float32))
    assert any(np.allclose(c, q, atol=1e-3) for q in p.colors)


def _chalk_spec():
    return S.normalise({"loop": False, "segments": [
        {"id": "A", "scene": "chalk_unify", "beats": 10, "params": {"left": "G_{μν} = 8πG T_{μν}", "right": "iħ ∂ψ/∂t = Ĥψ",
                                                                    "merge_at": 6, "tag": "subtle"}},
        {"id": "B", "scene": "chalk_unify", "beats": 7, "params": {"mode": "calendar", "year": 1980, "odds": "%50"}},
        {"id": "C", "scene": "chalk_unify", "beats": 8, "params": {"mode": "calendar", "year_from": 1980, "year_to": 2002,
                                                                    "odds_crossout_at": 2, "godel_note": "GÖDEL 1931", "tag": "legible"}}]})


def test_chalk_brand_tags_counted():
    s = _chalk_spec(); pl = S.brand_placements(s)
    tags = [(sid, kind, leg) for sid, at, kind, leg in pl if kind == "chalk_tag"]
    assert ("A", "chalk_tag", False) in tags and ("C", "chalk_tag", True) in tags and not any(t[0] == "B" for t in tags)


def test_chalk_board_persists_across_segments():
    from bitloop.scenes import SCENES
    s = _chalk_spec(); g = s["segments"][2]
    sc = SCENES["chalk_unify"](g["params"], 0, Palette(s["palette"]), ".").bind(g, s)
    st = sc._events(sc.gbeat(3.0))
    assert st["left"] and st["merge"] and st["merge"][0] == s["segments"][0]["start_beat"] + 6    # written in A, still there
    assert st["left"][0] < s["segments"][1]["start_beat"]                                          # never rewritten by B/C
    assert st["odds"] and st["cross"] == g["start_beat"] + 2 and st["cal"][0] == "flip" and st["tag"][1] == "legible"


def test_own_layers_counted_for_new_scenes():
    from bitloop.scenes import SCENES
    for k in ("cosmic_zoom", "chalk_unify", "galaxy_chess"):
        assert getattr(SCENES[k], "own_layers", 0) >= 2, k


def test_cosmic_chain_is_rigid_nesting():
    from bitloop.scenes import SCENES
    from bitloop.scenes_cosmos import ANCHOR
    s = S.normalise({"segments": [{"scene": "cosmic_zoom", "beats": 8, "params": {"from": "kid", "to": "web"}}]})
    g = s["segments"][0]; sc = SCENES["cosmic_zoom"](g["params"], 0, Palette(s["palette"]), ".").bind(g, s)
    for Z in (0.3, 1.5, 2.7, 3.6):
        Q = sc.chain(Z)
        for j in range(1, max(Q) + 1):
            if j - 1 in Q: assert np.allclose(Q[j - 1], (Q[j] - np.array(sc.anchor(j))) * 10.0, atol=1e-6), (Z, j)


def test_rewind_ends_on_frame0():
    from bitloop.render import Film
    s = S.normalise({"loop": True, "segments": [
        {"scene": "cosmic_zoom", "beats": 8, "role": "hook", "params": {"from": "kid", "to": "web"}, "layers": {"back": [], "front": []}},
        {"scene": "cosmic_zoom", "beats": 9, "params": {"from": "kid", "to": "kid", "stages": ["kid"], "kid_turns": True},
         "layers": {"back": [], "front": []}},
        {"scene": "cosmic_zoom", "beats": 3, "params": {"from": "kid", "to": "kid", "stages": ["kid"], "rewind_to_frame0": True},
         "layers": {"back": [], "front": []}, "layer_sync": "loop", "transition_in": "cut"}]})
    f = Film(s); i = 2; g = s["segments"][i]
    sc = f.scenes[i]; dur = g["end_beat"] - g["start_beat"]
    assert abs(sc.Z(dur, dur)) < 1e-9 and np.allclose(sc.view0(), sc.p["kid_view"])
    assert abs(sc.Z(0, dur) - sc.p["close_z"]) < 1e-9                              # starts on the S9 close-up
    diff = lambda x, y: (np.abs(x.astype(int) - y.astype(int)).sum(2) > 30).mean()
    T = s["duration_s"]
    assert diff(f.frame(T - 1 / 30), f.frame(0.0)) < .04


def _chess_spec():
    from bitloop.scenes_cosmos import rule_ca
    ca = rule_ca(30, 8, 16); vals = []
    for row in ca:
        on = [i for i, x in enumerate(row) if x] or [0]; vals += [on[k % len(on)] for k in range(4)]
    return S.normalise({"loop": False, "music": {"bpm": 100, "key": "E", "scale": "minor", "logo": False,
                        "series_defs": {"kural30": {"values": vals, "period": len(vals)}},
                        "voices": {"kural": {"role": "lead", "type": "pulse", "octave": 5, "series": {"name": "kural30", "rate": 4, "phase": "section"}}},
                        "sections": [{"beats": 3, "energy": 1, "voices": ["kural"]}, {"beats": 9, "energy": 2, "voices": ["kural"]}]},
                        "segments": [{"scene": "void", "beats": 3, "role": "hook"},
                                     {"scene": "galaxy_chess", "beats": 9, "params": {"ca_series": "kural30"}}]}), ca


def test_galaxy_chess_ca_synced_to_music():
    from bitloop.scenes import SCENES
    s, ca = _chess_spec(); g = s["segments"][1]
    sc = SCENES["galaxy_chess"](g["params"], 0, Palette(s["palette"]), ".").bind(g, s)
    assert sc.lights, "no series lights"
    b0 = s["_sections"][1]["b0"]
    for b, row, col, gen in sc.lights:
        n = round((b - b0) * 4); assert gen == n // 4 and row == gen % 8 and ca[gen % 16][col] == 1, (b, row, col, gen)
    # gen 2 lights exactly at b0 + 2 (± 1 frame) and not before
    L_before = sc._cell_light(2.0 - 1 / 30 / (60 / 100) - 1e-6); L_at = sc._cell_light(2.0)
    assert L_at[2].max() > 1.0 and L_before[2].max() == 0


def test_chaos_twins_split_at_diverge_at():
    from bitloop.scenes import SCENES
    s = S.normalise({"segments": [{"scene": "laplace_demon", "beats": 9,
                                   "params": {"balls": 2, "abacus": False, "chaos_twin": {"dx": 1e-4, "diverge_at": 3}}}]})
    g = s["segments"][0]; sc = SCENES["laplace_demon"](g["params"], 0, Palette(s["palette"]), ".").bind(g, s)
    frame_b = (1 / 30) / (60 / s["music"]["bpm"])
    assert abs(sc.t_split - 3.0) <= frame_b, sc.t_split
    X, Y, _ = sc._tw(sc._twin_at(2.5)); assert math.hypot(X[0] - X[1], Y[0] - Y[1]) < 1.0
    X, Y, _ = sc._tw(sc._twin_at(5.0)); assert math.hypot(X[0] - X[1], Y[0] - Y[1]) > 3.0


def test_encoder_writes_bt709_tags():
    from bitloop import render
    src = inspect.getsource(render)
    for k in ("-color_primaries\", \"bt709", "h264_metadata=colour_primaries=1", "-color_range\", \"tv"):
        assert k in src, k


def test_qc_phone_legibility_options_and_pose_continuity():
    """QC (evren-anlamak v2): formula_dot 2 writes the formulas ~2x wider (phone-legible subscripts) and the 5x7 label
    font is taller than the 3x5 micro-chalk; const_y moves the sky equations; rewind_turn starts the loop segment on
    the S9 close-up pose; far_ca / far_dots default to the old values."""
    from bitloop.scenes import SCENES
    from bitloop.scenes_chalk import _formula, _font, _mini
    from bitloop.render import Film
    ink = {}
    for fd in (1.0, 2.0):
        s = _chalk_spec(); s["segments"][0]["params"].update({"formula_dot": fd, "label_font": "font"} if fd == 2 else {})
        s["segments"] = s["segments"][:1]; s["loop"] = False
        f = Film(s); bpm = s["music"]["bpm"]; fr = f.frame(5.5 * 60 / bpm).astype(int)
        ink[fd] = ((fr.min(2) > 150)).sum()                     # pale chalk pixels (both formulas fully written)
    assert ink[2.0] > 2.5 * ink[1.0], ink
    assert _font("GÖRELİLİK").shape[0] > _mini("GÖRELİLİK").shape[0]
    s = S.normalise({"segments": [{"scene": "cosmic_zoom", "beats": 7, "params": {"stages": ["sky"], "constellations": "equations",
                                                                                 "const_y": [-112.0, -76.0, -40.0]}}]})
    g = s["segments"][0]; sc = SCENES["cosmic_zoom"](g["params"], 0, Palette(s["palette"]), ".").bind(g, s)
    ys = [y for path in sc._const_paths() for _, y in path]
    assert min(ys) < -112 + 1 - 17 / 2 + 1 and max(ys) < -40 + 14, (min(ys), max(ys))
    s = S.normalise({"segments": [{"scene": "cosmic_zoom", "beats": 3, "params": {"stages": ["kid"], "from": "kid", "to": "kid",
                                                                                 "rewind_to_frame0": True, "rewind_turn": [1.2, 1.9]}}]})
    g = s["segments"][0]; sc = SCENES["cosmic_zoom"](g["params"], 0, Palette(s["palette"]), ".").bind(g, s)
    assert sc._kid_frame(0.0, 0.0) == "front" and sc._kid_frame(1.5, 1.5) == "q" and sc._kid_frame(2.5, 2.5).startswith("up")
    from bitloop.scenes_cosmos import GalaxyChess
    assert GalaxyChess.defaults["far_ca"] == .55 and GalaxyChess.defaults["far_dots"] == .9


if __name__ == "__main__":
    for k, fn in list(globals().items()):
        if k.startswith("test_"): fn(); print("ok", k)
