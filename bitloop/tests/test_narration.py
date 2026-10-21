"""Narration text system + calm pacing. Run: python tests/test_narration.py"""
import json, os, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from bitloop import spec as S
from bitloop import narration as N

LONG = ("Bir kitap *geleceğini* biliyor olsaydı, _sen_ yine de seçer miydin? Laplace'a göre evren, "
        "her atomun yerini bilen bir zihin için tamamen öngörülebilir bir saat gibi işler ve yarın dün kadar nettir.")


def spec(nar, beats=16, loop=False, bpm=120, pacing=None, **seg):
    s = {"loop": loop, "brand": {"auto": False}, "music": {"bpm": bpm}, "segments": [
        {"id": "A", "role": "hook", "scene": "hero", "beats": beats, "narration": nar, **seg},
        {"id": "B", "role": "free", "scene": "network", "beats": 8, "transition_in": "dissolve"}]}
    if pacing: s["pacing"] = pacing
    return S.normalise(s)


def text_of(line): return " ".join("".join(c for c, _ in w) for w in line)


def test_measured_legibility_floor():
    assert N.min_legible_dot() == N.MIN_DOT == 5                       # 22′ cap height on a 5.4" phone @ 35 cm
    assert N.cap_arcmin(5) >= N.MIN_ARCMIN > N.cap_arcmin(4)
    assert N.recognition(N.MIN_DOT)[0] == 1.0
    assert min(N.SIZES.values()) >= N.MIN_DOT and N.SIZES["body"] < N.SIZES["head"] < N.SIZES["title"]
    s = spec([{"text": "Küçük yazı burada.", "size": 4, "at": 0}]); e, w = S.validate(s)
    assert any("below the legible minimum" in x for x in e)


def test_turkish_wrap_hyphenation_and_joins():
    b = N.normalise_block({"text": LONG + " 300 000 km hızla Elektromanyetikleştiremediklerimizden", "place": "dialog"})
    lines, dot, maxw, _ = N.block_lines(b)
    assert dot == 6 and all(N.line_w(l) <= maxw for l in lines)
    chars = [len(text_of(l)) for l in lines[:-1]]
    assert 20 <= sum(chars) / len(chars) <= 26, chars                 # ≈ 20–26 chars per body line
    flat = [text_of(l) for l in lines]
    assert any("300\u00a0000\u00a0km" in l for l in flat)               # numbers + unit never split
    hy = [l for l in flat if l.endswith("-")]
    assert hy and all(l.split()[-1][:-1].lower() in "elektromanyetikleştiremediklerimizden" for l in hy)
    def syl(word):
        br = N.syllable_breaks([(c, 0) for c in word]); return "-".join(word[a:b] for a, b in zip([0] + br, br + [len(word)]))
    assert syl("kitaplık") == "ki-tap-lık" and syl("türkçe") == "türk-çe" and syl("saatler") == "sa-at-ler"
    assert syl("geleceğini") == "ge-le-ce-ği-ni" and syl("kalem") == "ka-lem"     # (1-letter edge syllables are not split off)
    for l in flat[:-1]:                                                 # no 1–2-letter word left dangling at a line end
        assert len(l.split()[-1].strip(".,!?")) > 2 or l.endswith("-"), l
    assert N.tr_upper("istanbul ılık") == "İSTANBUL ILIK"
    assert N.missing("âîû ÂÎÛ çğıöşü ÇĞİÖŞÜ İ ı %40 3,14", "as_is") == [] and N.missing("istanbul", "upper") == []


def test_typewriter_units_on_16th_grid_and_blips_in_timeline():
    s = spec([{"text": "Saat *tik* tak, evren işler.", "at": 2, "place": "top", "rate": "16th", "blip": {"every": 2}}])
    B = N.blocks(s)[0]; p = B["t"]
    assert p["rate"] == .25 and p["lead"] == .25
    steps = sorted({u[3] for u in B["units"]})
    beats = [p["start"] + p["lead"] + k * p["rate"] for k in steps]
    assert all(abs(x * 4 - round(x * 4)) < 1e-9 for x in beats)          # every letter lands on a 16th
    assert len(steps) < len([u for u in B["units"]]) + 3                # pauses after , and . are extra steps
    bl = [b for b, k in B["blips"]]
    assert bl and set(round(x, 6) for x in bl) <= set(round(x, 6) for x in beats)
    ev = [e for e in S.timeline_events(s) if e[1].startswith("blip")]
    assert [round(e[0], 6) for e in ev] == [round(x, 6) for x in bl]
    for k in (0, 3, 7):                                                 # reveal state == step count at the grid point
        assert N.state(B, beats[k] + 1e-4)[2] == steps[k] + 1 and N.state(B, beats[k] - 1e-3)[2] <= steps[k]


def test_blip_audio_is_on_the_grid_and_quiet():
    from bitloop.music import synth, _read, SR
    s = S.normalise({"loop": False, "brand": {"auto": False}, "music": {"bpm": 120, "voices": {}, "drums": {"K": "................"}, "logo": False},
                     "segments": [{"id": "A", "scene": "hero", "beats": 16, "narration": [
                         {"text": "Tik tak tik tak tik tak", "at": 1, "rate": "8th", "blip": {"every": 1}, "until": 15}]}]})
    a = _read(synth(s, os.path.join(tempfile.mkdtemp(), "b.wav")))[:, 0]
    B = N.blocks(s)[0]; tm = __import__("bitloop.timing", fromlist=["tempo_map"]).tempo_map(s)
    env = np.abs(a)
    for b, k in B["blips"][:6]:
        i = int(tm.time(b) * SR); w = env[i - 240:i + 960]
        onset = (np.argmax(w > .3 * w.max()) - 240) / SR
        assert abs(onset) < .004, (b, onset)


def test_layout_avoids_subject_and_ui_safe_zones():
    from bitloop.render import Film
    W, H = 1080, 1920; x0, y0, x1, y1 = N.safe_rect(W, H)
    s = spec([{"text": LONG[:90], "at": 0}], subject=[-90, -160, 90, -60])   # subject fills the top third
    f = Film(s); B = f.narr.blocks[0]; r = B["rect"]
    assert B["placed"] != "top" and B["subject_cover"] < .05
    assert x0 <= r[0] and r[2] <= x1 and y0 <= r[1] and r[3] <= y1        # never under the bottom 18 % / right column
    s2 = spec([{"text": "Ne var?", "at": 0, "place": "top"}, {"text": "İkinci blok burada", "at": 0, "place": "top"}])
    a, b = [x["rect"] for x in Film(s2).narr.blocks[:2]]
    assert N._overlap(a, b) == 0                                          # simultaneous blocks stack, never overlap


def test_frames_palette_safe_cursor_and_exit():
    from bitloop.render import Film
    from bitloop.palette import Palette
    s = spec([{"text": "Seç *birini*, gerisi _hayal_.", "at": 0, "place": "dialog", "speaker": "ZAR", "rate": "16th", "until": 12, "exit": "wipe"},
              {"text": "BURASI", "at": 1, "place": "world", "reveal": "line", "surface": {"x": 0, "y": 40, "w": 60, "fill": True}, "until": 12},
              {"text": "hedef", "at": 2, "place": "callout", "target": "focus", "reveal": "word", "until": 12}])
    f = Film(s); pal = (Palette().colors * 255 + .5).astype(int)
    for t in (.3, 2.0, 5.5, 5.9):
        fr = f.frame(t); cols = np.unique(fr.reshape(-1, 3), axis=0)
        assert all((np.abs(pal - c).sum(1) <= 1).any() for c in cols), t
    B = f.narr.blocks[0]; R = B["R"]; tm = f.tm
    mid = N.paint(B, R, B["t"]["start"] + B["t"]["lead"] + 3 * .25 + 1e-3, f.narr.colors)
    full = N.paint(B, R, B["t"]["full"] + .1, f.narr.colors)
    txt = lambda im: (np.abs(im[..., :3].astype(int) - f.narr.colors[N.C_TEXT]).sum(-1) == 0) & (im[..., 3] > 0)
    assert 0 < txt(mid).sum() < txt(full).sum()
    ex = N.paint(B, R, B["t"]["exit0"] + .6 * (B["t"]["end"] - B["t"]["exit0"]), f.narr.colors)
    assert ex[:, : int(.5 * ex.shape[1]), 3].sum() == 0 and ex[..., 3].sum() > 0     # wipe clears left → right


def test_loop_seam_text_matches_frame_zero():
    from bitloop.render import Film
    s = spec([{"text": "Gelecek *yazılı* mı?", "at": 0, "place": "top", "rate": "16th"}], beats=12, loop=True)
    f = Film(s); T = f.T
    a, b = f.frame(0.0), f.frame(T - 1e-3)
    r = f.narr.blocks[0]["rect"]; reg = lambda im: im[r[1]:r[3], r[0]:r[2]].astype(int)
    assert np.abs(reg(a) - reg(b)).mean() < 12                         # same (empty) box at both sides of the seam


def test_validator_reading_time_and_old_rules_gone():
    short = spec([{"text": LONG[:120], "at": 0, "until": 6}]); e, w = S.validate(short)
    assert any("reading time" in x for x in w)
    ok = spec([{"text": "Kısa ve net bir cümle.", "at": 0, "rate": "32nd"}]); e, w = S.validate(ok)
    assert not any("reading time" in x for x in w)
    cap = S.normalise({"loop": False, "brand": {"auto": False}, "segments": [
        {"scene": "hero", "beats": 16, "role": "hook", "caption": {"text": "ON DÖRT HARFLİK\nİKİ SATIR VE DAHA FAZLA KELİME", "at": [0, 15]}}]})
    e, w = S.validate(cap)
    assert not any("aim ≤ 12" in x or "> 6 words" in x or "text on screen" in x for x in e + w)
    h = spec([{"text": "takip et @hayret.piksel", "at": 0}]); e, _ = S.validate(h)
    assert any("handle may not appear in narration" in x for x in e)


def test_calm_pacing_defaults_and_rules():
    s = spec([], pacing=None); p = s["_pace"]
    assert s["fx"]["shake"] == 1.0 and s["fx"]["flash"] <= .25 and s["crash_beats"] == 2.0 and p["layer_speed"] < 1
    old = spec([], pacing="punchy")
    assert old["fx"]["shake"] == 2.5 and old["fx"]["flash"] == .55 and old["crash_beats"] == 1.2
    w1 = S.normalise({"segments": [{"scene": "hero", "beats": 8}, {"scene": "hero", "beats": 8, "transition_in": "whip"}]})
    w0 = S.normalise({"pacing": "punchy", "segments": [{"scene": "hero", "beats": 8}, {"scene": "hero", "beats": 8, "transition_in": "whip"}]})
    assert w1["segments"][1]["_tr"]["beats"] > w0["segments"][1]["_tr"]["beats"] == .5
    hits = S.visual_hits(S.normalise({"segments": [{"scene": "hero", "beats": 8, "events": [{"at": 1, "kind": "punch"}]}]}))[1]
    assert hits[0][1] == .05
    busy = {"brand": {"auto": False}, "segments": [{"scene": "hero", "beats": 4, "role": "hook"}] +
            [{"scene": "hero", "beats": 3, "transition_in": t} for t in ("whip", "crash", "glitch", "spin", "flash", "whip")]}
    _, wc = S.validate(S.normalise(json.loads(json.dumps(busy))))
    _, wp = S.validate(S.normalise({**json.loads(json.dumps(busy)), "pacing": "punchy"}))
    assert any("fast transitions" in x for x in wc) and not any("fast transitions" in x for x in wp)
    assert any("segments average" in x for x in wc)
    cam = S.normalise({"brand": {"auto": False}, "segments": [{"scene": "hero", "beats": 4, "role": "hook"},
                                                              {"scene": "hero", "beats": 4, "camera": {"zoom": [2.5, 1.0]}}]})
    assert any("fast camera" in x for x in S.validate(cam)[1])


def test_text_reveal_counts_as_visual_change():
    plain = spec([], beats=10, bpm=100); typed = spec([{"text": LONG[:110], "at": 0, "rate": "16th"}], beats=10, bpm=100)
    g0 = max(d for d, a in S.retention(plain)["gaps"]); g1 = max(d for d, a in S.retention(typed)["gaps"])
    assert g0 > 5 and g1 < 4.5


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"): v(); print("ok", k)
