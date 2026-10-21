"""matematik-edm: writes spec.json (TARGET: new `formula_scope` scene — a neon XY oscilloscope plotting each brief
function exactly, with per-section EDM voices) and spec_proxy.json (same timeline on the existing `noise_scope`)
for validate/sheet/music smoke test. Pacing: punchy (11 scenes in 20 s). Palette: neon (custom, black + magenta)."""
import copy, json
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))
from palettes import PALETTES

BPM = 120
PAL = PALETTES["neon"]

# scene label (top) + formula (bottom, ASCII + π + ·; 1 dot = 6 screen px)
F = {
    "hardtekk": "y = mod(8t,1) > 0.9\n? 1 : -1",
    "phonk808": "y = sin(2π·39t)·exp(-3t)\n·tanh(10·sin(2π·0.5t))",
    "acid":     "y = sign(sin(2π·4t))\n·exp(-0.5·mod(t,0.25))",
    "funk":     "y = sin(2π·2t)\n+ 0.5·sin(2π·6t+π/4)",
    "phonkmel": "y = sin(2π·(220\n+50·sin(2π·0.3t))·t)",
    "jersey":   "y = mod(12t,1) < 0.3\n? sin(2π·200t) : 0",
    "trance":   "y = sin(2π·440·2^mod(2t,1)·t)\n·exp(-2·mod(t,0.5))",
    "psy":      "y = sin(2π·65t)\n·(0.5+0.5·sign(sin(2π·8t)))",
    "build":    "y = sin(2π·(100+50t)·t)\n·(t/3)",
}


def seg(**k):
    k.setdefault("layers", {"back": ["grid", "nebula"], "front": ["dust"]})
    k.setdefault("events", [])
    return k


spec = {
 "version": 2,
 "meta": {
  "title": "Her Ses = Tek Bir Grafik: Matematikle EDM 🎧",
  "description": ("Dokuz matematik fonksiyonu, dokuz ayrı elektronik ses karakteri... ve finalde hepsi tek bir parçada "
                  "birleşiyor. Gördüğün eğri, duyduğun sesin ta kendisi: 39 Hz'lik 808'den 440 Hz'lik trance "
                  "arpejine. Sence hangisi en sert? 👇"),
  "hashtags": ["#matematik", "#elektronikmüzik", "#edm", "#pixelart", "#chiptune", "#hayretpiksel"],
  "lang": "tr", "cover_t": 19.4,
 },
 "format": {"w": 1080, "h": 1920, "fps": 30, "grid": 6},
 "pacing": "punchy",
 "palette": PAL,
 "narration_defaults": {"reveal": "word", "rate": "8th", "size": "head", "place": "top", "case": "upper"},
 "readability": {"per_word": 0.35, "base": 0.6},
 "music": {
  "bpm": BPM, "meter": "4/4", "key": "F", "scale": "phrygian_dominant", "tuning": "12tet", "flavour": "sid",
  "progression": [["F2", "Ab2", "C3"], ["F2", "Ab2", "Db3"]], "chord_bars": 2, "swing": 0, "seed": 2026,
  "hf_shelf_db": -3.0,
  "voices": {
   "bass":  {"role": "bass", "type": "pulse", "duty": 0.5, "octave": 2, "vol": 0.06, "pattern": "root8", "filter": "soft"},
   "b808":  {"role": "bass", "type": "triangle", "octave": 1, "vol": 0.075, "filter": "soft",
             "env": {"a": .002, "d": .35, "s": .15, "r": .35}},
   "acid":  {"role": "arp", "type": "pulse", "duty": 0.25, "octave": 4, "vol": 0.05, "pattern": "updown", "rate": 4, "filter": "soft"},
   "funk":  {"role": "bass", "type": "pulse", "duty": 0.3, "octave": 2, "vol": 0.06, "pattern": "walk", "rate": 2, "filter": "soft"},
   "mel":   {"role": "lead", "type": "fm", "ratio": 1.5, "index": 2.0, "octave": 5, "vol": 0.05, "pan": 0.1},
   "arp":   {"role": "arp", "type": "pulse", "duty": 0.125, "octave": 5, "vol": 0.045, "pattern": "up", "rate": 4, "filter": "soft"},
   "psy":   {"role": "bass", "type": "pulse", "duty": 0.5, "octave": 2, "vol": 0.065, "pattern": "root8", "rate": 4, "filter": "soft"},
   "pad":   {"role": "pad", "type": "saw", "octave": 3, "vol": 0.02, "filter": "soft"},
   "lead": None, "counter": None,
  },
  "drums": {"K": "X...............", "H": "..x...x...x...x."},
  "sections": [
   {"name": "giris",     "beats": 2, "energy": 0.8, "voices": ["pad"], "drums": "none"},
   {"name": "hardtekk",  "beats": 4, "energy": 2.2, "voices": ["bass", "pad"],
    "drums": {"K": "X...X...X...X...", "H": "..x...x...x...x."}},
   {"name": "phonk808",  "beats": 4, "energy": 2.4, "voices": ["b808", "bass"],
    "drums": {"K": "X.......X.......", "S": "....o.......o..."}},
   {"name": "acid",      "beats": 4, "energy": 2.6, "voices": ["acid", "bass"],
    "drums": {"K": "X...X...X...X...", "H": "x.x.x.x.x.x.x.x."}},
   {"name": "funk",      "beats": 4, "energy": 2.7, "voices": ["funk", "bass"],
    "drums": {"K": "X...X.x.X...X.x.", "H": "..x...x...x...x.", "S": "....o.......o..."}},
   {"name": "phonkmel",  "beats": 4, "energy": 2.8, "voices": ["mel", "bass"], "drums": "boom_bap"},
   {"name": "jersey",    "beats": 4, "energy": 3.0, "voices": ["acid", "bass"],
    "drums": {"K": "X.XX.X.XX.XX.X..", "H": "xxxxxxxxxxxxxxxx", "S": "....o.......o..."}},
   {"name": "trance",    "beats": 4, "energy": 3.2, "voices": ["arp", "bass", "pad"], "drums": "four_on_floor"},
   {"name": "psy",       "beats": 4, "energy": 3.4, "voices": ["psy", "arp"], "drums": "four_on_floor"},
   {"name": "build",     "beats": 4, "energy": 3.7, "voices": ["arp", "bass"], "riser": True, "riser_kind": "noise",
    "drums": {"K": "X...............", "S": "....x...x...x.x."}},
   {"name": "drop",      "beats": 2, "energy": 4.2, "drop": True,
    "voices": ["bass", "b808", "acid", "funk", "mel", "arp", "psy", "pad"],
    "drums": {"K": "X...X...X...X...", "S": "....X.......X...", "H": "x.x.x.x.x.x.x.x."}},
  ],
  "logo": {"at": ["reveal", "loop"], "voice": "mel"},
 },
 "brand": {"handle": "@hayret.piksel", "auto": False},
 "loop": True, "loop_beats": 1.0, "loop_transition": {"type": "dissolve", "beats": 1},
 "segments": [
  seg(id="S0", role="hook", scene="formula_scope", beats=2,
      params={"formula": "hardtekk", "formula_text": "", "window": 0.9},
      transition_in="cut",
      narration=[{"text": "matematikle elektronik müzik", "at": 0, "place": "title", "size": "head", "rate": "16th"}]),
  seg(id="S1", role="step", scene="formula_scope", beats=4,
      params={"formula": "hardtekk", "formula_text": F["hardtekk"]},
      transition_in="whip",
      events=[{"at": 0, "kind": "shake"}, {"at": 2, "kind": "rehook"}],
      narration=[{"text": "hardtekk kick", "at": 0}]),
  seg(id="S2", role="step", scene="formula_scope", beats=4,
      params={"formula": "phonk808", "formula_text": F["phonk808"]},
      transition_in="cut",
      narration=[{"text": "phonk 808", "at": 0}]),
  seg(id="S3", role="step", scene="formula_scope", beats=4,
      params={"formula": "acid", "formula_text": F["acid"]},
      transition_in="slide",
      narration=[{"text": "acid bassline", "at": 0}]),
  seg(id="S4", role="step", scene="formula_scope", beats=4,
      params={"formula": "funk", "formula_text": F["funk"]},
      transition_in="cut",
      narration=[{"text": "funk ritmi", "at": 0}]),
  seg(id="S5", role="step", scene="formula_scope", beats=4,
      params={"formula": "phonkmel", "formula_text": F["phonkmel"]},
      transition_in="slide",
      events=[{"at": 0, "kind": "twist", "label": "melodi girer: ses = grafik"}],
      narration=[{"text": "phonk melodisi", "at": 0}]),
  seg(id="S6", role="step", scene="formula_scope", beats=4,
      params={"formula": "jersey", "formula_text": F["jersey"]},
      transition_in="cut",
      events=[{"at": 0, "kind": "shake"}, {"at": 2, "kind": "rehook"}],
      narration=[{"text": "jersey club", "at": 0}]),
  seg(id="S7", role="step", scene="formula_scope", beats=4,
      params={"formula": "trance", "formula_text": F["trance"]},
      transition_in="slide",
      narration=[{"text": "trance arpeggio", "at": 0}]),
  seg(id="S8", role="step", scene="formula_scope", beats=4,
      params={"formula": "psy", "formula_text": F["psy"]},
      transition_in="cut",
      narration=[{"text": "psytrance bass", "at": 0}]),
  seg(id="S9", role="build", scene="formula_scope", beats=4,
      params={"formula": "build", "formula_text": F["build"]},
      transition_in="glitch",
      events=[{"at": 0, "kind": "shake"}],
      narration=[{"text": "hazır mısın?", "at": 1}]),
  seg(id="S10", role="reveal", scene="formula_scope", beats=2,
      params={"formula": "all", "formula_text": ""},
      props=[{"kind": "plate", "x": 0, "y": 88, "s": 1.4, "model": "MAT-LAB", "layer": "front", "par": 1.0,
              "from": 0.4, "legible": True}],
      transition_in="crash",
      events=[{"at": 0, "kind": "reveal", "label": "drop: tüm katmanlar"}],
      narration=[{"text": "her ses = tek bir grafik", "at": 0, "place": "title", "size": "head", "rate": "16th"}]),
 ]}

json.dump(spec, open("spec.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------- proxy: existing scene only (noise_scope = a lab oscilloscope), same timeline/music/narration
px = copy.deepcopy(spec)
for g in px["segments"]:
    g["scene"] = "noise_scope"
    g["params"] = {"traces": ["pink"], "x": 0, "y": 8, "w": 150, "h": 140}
    for e in g.get("events", []):
        e.pop("label", None)
json.dump(px, open("spec_proxy.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ok", sum(g["beats"] for g in spec["segments"]), "beats =",
      round(sum(g["beats"] for g in spec["segments"]) * 60 / BPM, 2), "s")
