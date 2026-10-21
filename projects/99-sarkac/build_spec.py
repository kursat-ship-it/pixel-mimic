"""99-sarkac: writes spec.json (TARGET: new `pendulum_grid` scene — 99 Kuramoto-coupled pendulums in a 9×11 grid,
order-parameter reveal, one 17:16 outlier) and spec_proxy.json (same timeline on the existing `network` scene)
for validate / sheet / music smoke test. Pacing: calm. Text: narration blocks (recipe §12.6, RESEARCHER_GUIDE).

One beat clock: 120 BPM 4/4 → 1 beat = 0.5 s → 30 beats = 15.0 s exactly (brief's length)."""
import copy, json
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # outputs land next to this file

BPM = 120
# sonic logo 5→1→2→3 in A dorian, played by the lead timbre at reveal + loop
MOTIF = {"notes": [4, 0, 1, 2, None], "rhythm": [0.5]}

# dark atmospheric backdrop + ambient motes = ≥ 3 moving layers (back: stars + nebula, front: dust)
LAYERS = {"back": ["stars", "nebula"], "front": ["dust"]}

# legible diegetic tag: a lab plate on the pendulum apparatus base (draws @hayret.piksel), revealed with the drop
PLATE = {"kind": "plate", "x": 0, "y": 72, "s": 1.4, "model": "SARKAÇ 99", "layer": "front", "par": 1.0,
         "from": 2.0, "legible": True}


def seg(**k):
    k.setdefault("layers", dict(LAYERS))
    k.setdefault("events", [])
    return k


spec = {
 "version": 2,
 "meta": {
  "title": "99 Sarkaç Senkronize Olurken, Biri Farklı Kalıyor 🎧",
  "description": ("99 özdeş sarkaç, Kuramoto çiftlenmesiyle kendiliğinden senkronize olur; ama doğal frekansı 17/16 "
                  "olan biri dışarıda kalır. Düzen parametresi R(t)=|Σe^{iφⱼ}|/99 bu 'kaostan düzene' geçişi ölçer — "
                  "sence hangisi farklı? 👇"),
  "hashtags": ["#bilim", "#matematik", "#senkronizasyon", "#pixelart", "#chiptune", "#hayretpiksel"],
  "lang": "tr", "cover_t": 13.0,
 },
 "format": {"w": 1080, "h": 1920, "fps": 30, "grid": 6},
 "pacing": "calm",
 "palette": "hayret",
 "narration_defaults": {"reveal": "word", "rate": "8th", "size": "head", "place": "top", "case": "upper"},
 "readability": {"per_word": 0.35, "base": 0.6},
 "music": {
  # Minimal electronic: the TICKS are the beat. Chaos → polyrhythmic ticks (scene sfx), R(t) rises → ticks lock
  # onto the grid, drop = one coherent rhythm + the sonic logo. The outlier ticks a semitone up, just off the beat.
  "bpm": BPM, "meter": "4/4", "key": "A", "scale": "dorian", "tuning": "12tet", "flavour": "fm",
  "progression": [["A3", "C4", "E4"], ["G3", "B3", "D4"]], "chord_bars": 2, "swing": 0, "seed": 99,
  "hf_shelf_db": -3.0, "motif": MOTIF,
  "voices": {
   "pad":   {"role": "pad",  "type": "fm", "ratio": 1.0, "index": 1.0, "octave": 3, "vol": 0.03, "filter": "soft",
             "env": {"a": .3, "d": .8, "s": .7, "r": .4}},
   "bass":  {"role": "bass", "type": "triangle", "octave": 2, "vol": 0.06, "pattern": "root8", "filter": "soft"},
   "lead":  {"role": "lead", "type": "fm", "ratio": 2.0, "index": 0.6, "octave": 5, "vol": 0.05, "pan": 0.1,
             "env": {"a": .004, "d": .2, "s": .5, "r": .1}},
   "counter": None, "arp": None,
  },
  "drums": {"K": "X..............."},
  "sections": [
   {"name": "kaos",      "beats": 6, "energy": 1.2, "voices": ["pad", "bass"], "drums": "none"},
   {"name": "beliriyor", "beats": 6, "energy": 1.6, "voices": ["pad", "bass"], "drums": {"K": "X.......X......."}},
   {"name": "dalgalar",  "beats": 6, "energy": 2.0, "voices": ["pad", "bass", "lead"],
    "drums": {"K": "X...X...X...X...", "H": "....x.......x..."}},
   {"name": "yaklasma",  "beats": 6, "energy": 2.4, "voices": ["pad", "bass", "lead"],
    "riser": True, "riser_kind": "shepard", "drums": {"K": "X...X...X...X...", "H": "..x...x...x...x.", "S": "....o.......o..."}},
   {"name": "kilit",     "beats": 6, "energy": 3.0, "drop": True, "voices": ["pad", "bass", "lead"],
    "drums": {"K": "X...X...X...X...", "S": "....X.......X...", "H": "..x...x...x...x."}},
  ],
  "logo": {"at": ["reveal", "loop"], "voice": "lead"},
 },
 "brand": {"handle": "@hayret.piksel", "auto": False},
 "loop": True, "loop_beats": 1.0, "loop_transition": {"type": "dissolve", "beats": 1},
 "segments": [
  seg(id="S1", role="hook", scene="pendulum_grid", beats=6,
      params={"rows": 11, "cols": 9, "phase": "chaos"},
      transition_in="cut",
      narration=[{"text": "99 sarkaç. biri farklı.", "at": 0},
                 {"text": "bulabilir misin?", "at": 4}]),
  seg(id="S2", role="rehook", scene="pendulum_grid", beats=6,
      params={"rows": 11, "cols": 9, "phase": "emerge"},
      transition_in="dissolve",
      narration=[{"text": "ipucu: ritmi takip et.", "at": 2}]),
  seg(id="S3", role="step", scene="pendulum_grid", beats=6,
      params={"rows": 11, "cols": 9, "phase": "waves"},
      transition_in="match",
      narration=[{"text": "her tik, bir titreşim.", "at": 0},
                 {"text": "kaos nasıl düzene dönüşüyor?", "at": 4}]),
  seg(id="S4", role="twist", scene="pendulum_grid", beats=6,
      params={"rows": 11, "cols": 9, "phase": "converge"},
      transition_in="glitch",
      events=[{"at": 2, "kind": "twist", "label": "biri hâlâ farklı"}],
      narration=[{"text": "ama biri hâlâ farklı...", "at": 2}]),
  seg(id="S5", role="reveal", scene="pendulum_grid", beats=6,
      params={"rows": 11, "cols": 9, "phase": "lock",
              "outlier_ring": {"at": 26, "beats": 1},
              "formula": {"text": "R(t) = |Σ e^(iφj)| / 99", "at": 28, "dot": 1.0, "y": 94},
              "freeze": {"at": 29, "beats": 1}},
      props=[dict(PLATE)],
      transition_in="iris",
      events=[{"at": 0, "kind": "reveal", "label": "drop + sonic logo"},
              {"at": 2, "kind": "flash", "label": "kırmızı halka aykırıyı kilitler"}],
      narration=[{"text": "gördün mü?", "at": 0},
                 {"text": "17'ye karşı 16!", "at": 2},
                 {"text": "kaosun içindeki düzen.", "at": 4}]),
 ]}

json.dump(spec, open("spec.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------- proxy: existing scene only (network = a grid of 99 moving nodes stands in for the pendulum grid)
px = copy.deepcopy(spec)
for g in px["segments"]:
    g["scene"] = "network"
    g["params"] = {"nodes": 99}
json.dump(px, open("spec_proxy.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ok", sum(g["beats"] for g in spec["segments"]), "beats =",
      round(sum(g["beats"] for g in spec["segments"]) * 60 / BPM, 2), "s")
