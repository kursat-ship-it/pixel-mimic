"""sesin-kumda-desenleri: Chladni figures — sand on a vibrating plate reveals the nodal lines of a standing wave.
New `chladni` scene: particles seeded once, pulled to the nearest nodal line over ~1 s; the plate mode (n,m) rises with
the driving tone so the shape you see and the pitch you hear share the same resonance (mode order n²+m²).
20 s = 40 beats @ 120 BPM, calm pacing. Writes spec.json (target) + spec_proxy.json (existing scene) for CI."""
import copy, json
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))

BPM = 120


def seg(**k):
    k.setdefault("events", [])
    return k


def ch(**k):
    # defaults shared by every chladni segment
    p = {"x": 0.0, "y": 0.0, "w": 140.0, "h": 140.0, "particles": 1600, "settle_s": 1.0,
         "label_dot": 1.0, "label_y": -80.0, "driver_y": 78.0}
    p.update(k)
    return p


spec = {
 "version": 2,
 "meta": {
  "title": "Sesin Kumda Çizdiği Gizli Desenler 🎧",
  "description": ("Ses görünmez... ama kum onu ele verir. Titreyen bir plakanın üstündeki kum, sesin çizdiği nodal "
                  "çizgilerde toplanır: Chladni desenleri. Frekans değiştikçe desen de değişir. Sence sesin şekli nasıl? 👇"),
  "hashtags": ["#bilim", "#ses", "#chladni", "#pixelart", "#chiptune", "#hayretpiksel"],
  "lang": "tr", "cover_t": 17.2,
 },
 "format": {"w": 1080, "h": 1920, "fps": 30, "grid": 6},
 "pacing": "calm",
 "palette": "hayret",
 "narration_defaults": {"reveal": "word", "rate": "8th", "size": "head", "place": "top", "case": "upper"},
 "music": {
  "bpm": BPM, "meter": "4/4", "key": "A", "scale": "natural_minor", "tuning": "12tet", "flavour": "fm",
  "progression": [["A3", "C4", "E4"]], "chord_bars": 2, "seed": 1787, "hf_shelf_db": -3.0,
  "voices": {
   "drone": {"role": "bass", "type": "triangle", "octave": 2, "vol": 0.08, "pattern": "sustain", "filter": "soft"},
   "lead":  {"role": "lead", "type": "fm", "ratio": 1.0, "index": 0.6, "octave": 5, "vol": 0.055,
             "env": {"a": .02, "d": .3, "s": .5, "r": .25}},
   "pad":   {"role": "pad", "type": "fm", "ratio": 2.0, "index": 0.7, "octave": 3, "vol": 0.03, "filter": "soft",
             "env": {"a": .4, "d": .8, "s": .6, "r": .5}},
   "counter": None, "arp": None,
  },
  "drums": {"K": "X..............."},
  "sections": [
   {"name": "giris",  "beats": 4, "energy": 1.0, "voices": ["pad"], "drums": "none"},
   {"name": "ortaya", "beats": 6, "energy": 1.4, "voices": ["pad", "drone"], "drums": "none"},
   {"name": "harita", "beats": 6, "energy": 1.8, "voices": ["pad", "drone", "lead"], "drums": "none"},
   {"name": "gizli",  "beats": 6, "energy": 2.2, "voices": ["pad", "drone", "lead"], "drums": "none"},
   {"name": "yogun",  "beats": 6, "energy": 2.6, "voices": ["pad", "drone", "lead"], "drums": "none"},
   {"name": "build",  "beats": 5, "energy": 3.0, "voices": ["pad", "drone", "lead"], "riser": True, "riser_kind": "shepard",
    "drums": "none"},
   {"name": "reveal", "beats": 5, "energy": 3.4, "drop": True, "voices": ["pad", "drone", "lead"], "drums": "none"},
   {"name": "dongu",  "beats": 2, "energy": 1.6, "voices": ["pad", "drone"], "drums": "none"},
  ],
  "logo": {"at": ["reveal", "loop"], "voice": "lead"},
 },
 "brand": {"handle": "@hayret.piksel", "auto": False},
 "loop": True, "loop_beats": 1.0, "loop_transition": {"type": "dissolve", "beats": 1},
 "segments": [
  seg(id="S1", role="hook", scene="chladni", beats=4, params=ch(n=1, m=1, label="mod 1,1"),
      transition_in="cut",
      narration=[{"text": "ses görünmez. kum?", "at": 0}]),
  seg(id="S2", role="step", scene="chladni", beats=6, params=ch(n=2, m=1, label="mod 2,1"),
      transition_in="dissolve",
      narration=[{"text": "ama kum onu ele verir.", "at": 0}]),
  seg(id="S3", role="step", scene="chladni", beats=6, params=ch(n=2, m=2, label="mod 2,2"),
      transition_in="match",
      events=[{"at": 0, "kind": "rehook"}],
      narration=[{"text": "her frekansın bir şekli vardır.", "at": 0}]),
  seg(id="S4", role="step", scene="chladni", beats=6, params=ch(n=3, m=2, label="mod 3,2"),
      transition_in="dissolve",
      narration=[{"text": "bu desen, sesin haritasıdır.", "at": 0}]),
  seg(id="S5", role="twist", scene="chladni", beats=6, params=ch(n=4, m=3, label="mod 4,3"),
      transition_in="glitch",
      events=[{"at": 0, "kind": "twist", "label": "kum titremeyen yere kaçar"}],
      narration=[{"text": "kum, titremeyen yere kaçar.", "at": 0}]),
  seg(id="S6", role="build", scene="chladni", beats=5, params=ch(n=5, m=3, label="mod 5,3"),
      transition_in="dissolve",
      events=[{"at": 0, "kind": "rehook"}],
      narration=[{"text": "frekans yükseldikçe desen çoğalır.", "at": 0}]),
  seg(id="S7", role="reveal", scene="chladni", beats=5, params=ch(n=4, m=4, label="mod 4,4"),
      props=[{"kind": "plate", "x": 0, "y": 88, "s": 1.3, "model": "KUM LAB", "layer": "front", "par": 1.0,
              "from": 1.0, "legible": True}],
      transition_in="iris",
      events=[{"at": 0, "kind": "reveal", "label": "sesin gizli deseni"}],
      narration=[{"text": "işte sesin gizli deseni.", "at": 0, "place": "title", "size": "title", "rate": "16th"}]),
  seg(id="S8", role="loop", scene="chladni", beats=2, params=ch(n=1, m=1, label="mod 1,1"),
      transition_in="dissolve", layer_sync="first"),
 ]}

json.dump(spec, open("spec.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# proxy: existing scene only (series_tree draws a recursive tree; it exercises layers/props/music), same timeline
px = copy.deepcopy(spec)
for g in px["segments"]:
    g["scene"] = "series_tree"
    g["params"] = {}
    for e in g.get("events", []):
        e.pop("label", None)
json.dump(px, open("spec_proxy.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ok", sum(g["beats"] for g in spec["segments"]), "beats =",
      round(sum(g["beats"] for g in spec["segments"]) * 60 / BPM, 2), "s")
