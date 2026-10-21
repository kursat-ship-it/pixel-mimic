"""canli-gozu: writes spec.json (TARGET: new `vision_world` / `vision_mosaic` scenes + per-segment vision modes,
pad max_notes, bat-chirp drum 'B') and spec_proxy.json (same timeline on existing features: `image` scene showing
the mock vision stills from vision_mock.py, union palette) for validate / sheet / music smoke test.
Pacing: calm (default). Text: narration blocks (recipe §12.6, RESEARCHER_GUIDE)."""
import copy, json
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # outputs land next to this file
from visions import VISIONS, ORDER, union_palette

BPM = 108
MOTIF = {"notes": [4, 0, 1, 2, None, 2, 4, None], "rhythm": [0.5]}   # the 'eye motif' = sonic logo 5→1→2→3 + answer

def seg(**k):
    k.setdefault("layers", {"back": ["rays", "horizon"], "front": ["dust", "bokeh"]})
    k.setdefault("events", []); return k

# vision_world paints its own sky/hills/meadow: back layers are drawn INTO the world (albedo, world palette) and show
# through the semi-transparent sky; front layers are drawn after the vision map in the mode's palette ("eye floaters").
DAY_L = {"back": [{"kind": "rays", "x": 56, "y": -122, "par": 1.0, "n": 7}], "front": ["dust", "pollen"]}
NIGHT_L = {"back": ["stars", {"kind": "nebula", "ramps": ["dim", "pale"]}], "front": ["dust"]}
HIVE_LABEL = {"kind": "plate", "skin": "hive", "x": 50, "y": 2, "s": 1.4, "model": "KOVAN 07", "layer": "mid", "par": 1.0,
              "depth": 0.21}

spec = {
 "version": 2,
 "meta": {"title": "Aynı Dünya, 6 Farklı Göz: Hayvanlar Ne Görüyor? 👁️",
          "description": ("Arı morötesini görür, köpek iki renk kanalıyla, yılan ısıyı, yarasa yankıyı... "
                          "Mantis karidesinin 12 renk alıcısı var ama birbirine yakın renkleri bizden kötü ayırt ediyor: 12–25 nm'lik farkı seçemiyor, biz birkaç nanometrelik farkı seçebiliyoruz (Thoen ve ark., 2014). "
                          "Videodaki renkler bilimsel verilere dayanan ÇEVİRİLER: bir hayvanın gerçekte ne yaşadığını bilemeyiz (Nagel, 1974). "
                          "Kelebek Graphium sarpedon'un gözünde 15 tür ışık alıcısı var, ama gündelik renk görüşünde muhtemelen 4 sınıf kullanıyor (Chen ve ark., 2016): alıcı sayısı ≠ renk sayısı. "
                          "Sence hangisi en tuhaf? 👇"),
          "hashtags": ["#bilim", "#hayvanlar", "#görme", "#pikselsanat", "#chiptune", "#hayretpiksel"], "cover_t": 37.5},
 "format": {"w": 1080, "h": 1920, "fps": 30, "grid": 6},
 "pacing": "calm",
 "palette": "hayret",
 "visions": {k: {kk: vv for kk, vv in v.items()} for k, v in VISIONS.items()},
 "world_palette": VISIONS["insan"]["palette"],
 "narration_defaults": {"reveal": "word", "rate": "16th"},
 "readability": {"per_word": 0.35, "base": 0.6},
 "music": {
  "_concept": ("ONE melody = the world; every creature 'hears' it through its own eye. The eye motif (sonic logo 5→1→2→3 + "
               "answer) is replayed per section in that creature's SCALE and TIMBRE, and the pad's NUMBER OF NOTES = number "
               "of colour channels: human triad (3), bee triad shifted up into lydian sparkle (3, UV = 'above us'), dog open "
               "fifth with no third (2), snake one low warm drone (heat), bat: no harmony — the CLICKS are the beat and they "
               "accelerate into a feeding buzz, mantis shrimp: a 12-note chromatic cluster that COLLAPSES to a bare octave on "
               "the twist ('12 receptors, poor discrimination'). Drop = all timbres at once in D lydian; Nagel = near silence, "
               "one sonar ping + human triad; sonic logo at drop and loop seam."),
  "bpm": BPM, "meter": "4/4", "key": "D", "scale": "major", "tuning": "12tet", "flavour": "gameboy",
  "progression": [["D3", "F#3", "A3"]], "chord_bars": 2, "swing": 0, "seed": 1974,
  "hf_shelf_db": -3.0, "motif": MOTIF,
  "voices": {
   "goz":     {"role": "lead", "type": "pulse", "duty": 0.25, "octave": 5, "vol": 0.07, "pan": 0.1, "env": {"a": .004, "d": .2, "s": .45, "r": .08},
               "_note": "human: plain pulse lead, the reference timbre"},
   "vizilti": {"role": "lead", "type": "pulse", "duty": 0.125, "octave": 6, "vol": 0.05, "pan": 0.15, "vibrato": 0.3, "vib_delay": 0.0,
               "env": {"a": .002, "d": .12, "s": .5, "r": .05}, "_note": "bee: thin 12.5% pulse, octave up, fast vibrato = wing buzz"},
   "kuyruk":  {"role": "lead", "type": "triangle", "octave": 5, "vol": 0.085, "pan": -0.1, "env": {"a": .002, "d": .14, "s": .3, "r": .05},
               "_note": "dog: round triangle, bouncy, pentatonic (fewer 'colours')"},
   "isi":     {"role": "lead", "type": "fm", "ratio": 1.0, "index": 2.6, "idecay": 2, "octave": 4, "vol": 0.06, "pan": 0.0, "vibrato": 0.15,
               "vib_delay": 0.2, "env": {"a": .05, "d": .4, "s": .6, "r": .2}, "_note": "snake: warm low FM, slow heat-shimmer vibrato, phrygian"},
   "sonar":   {"role": "lead", "type": "fm", "ratio": 7.0, "index": 3.5, "idecay": 30, "octave": 6, "vol": 0.045, "pan": -0.2, "echo": 0.75,
               "env": {"a": .001, "d": .06, "s": 0.0, "r": .03}, "_note": "bat: pings with an echo 3 8ths later (call → echo)"},
   "prizma":  {"role": "arp", "type": "pulse", "duty": 0.125, "octave": 5, "vol": 0.035, "pattern": "up", "rate": 4, "pan": -0.3,
               "_note": "mantis: 16th arp racing through the 12-note cluster"},
   "bass":    {"role": "bass", "type": "pulse", "duty": 0.5, "octave": 3, "vol": 0.056, "pattern": "octave", "rate": 2, "filter": "soft",
               "_note": "pulse bass (phone speakers, QC lesson), octave 3"},
   "pad":     {"role": "pad", "type": "saw", "octave": 4, "vol": 0.022, "filter": "soft", "env": {"a": .15, "d": .6, "s": .6, "r": .3},
               "max_notes": 12, "_note": "NEW max_notes (engine caps pads at 4 notes): number of pad notes = number of colour channels"},
   "lead": None, "counter": None, "arp": None},
  "drums": {"K": "X.......X.......", "H": "..x...x...x...x.", "S": "....o.......o..."},
  "sections": [
   {"name": "insan",    "beats": 8,  "energy": 1.6, "scale": "major", "progression": [["D3", "F#3", "A3"]], "voices": ["goz", "bass", "pad"]},
   {"name": "ari",      "beats": 10, "energy": 1.9, "scale": "lydian", "progression": [["E4", "G#4", "B4"]], "fill": True,
    "voices": ["vizilti", "bass", "pad"], "drums": {"K": "X.......X.......", "H": "x.x.x.x.x.x.x.x.", "S": "....o.......o..."}},
   {"name": "kopek",    "level_db": -1.0, "beats": 10, "energy": 1.9, "scale": "pentatonic_major", "progression": [["D3", "A3"]], "fill": True,
    "voices": ["kuyruk", "bass", "pad"], "drums": {"K": "X...X.x.X...X.x.", "H": "..x...x...x...x.", "S": "....o.......o..."}},
   {"name": "yilan",    "level_db": -1.5, "beats": 10, "energy": 2.0, "scale": "phrygian", "progression": [["D2", "A2"]], "fill": True,
    "voices": ["isi", "bass", "pad"], "drums": "half_time"},
   {"name": "yarasa",   "level_db": -1.0, "beats": 10, "energy": 2.3, "scale": "pentatonic_minor", "progression": [["D3", "A3"]], "stop": 0.5,
    "voices": ["sonar", "bass"],
    "drums": {"K": "X.......X.......", "B": "x...x...x.x.x.x.x.x.x.x.rrrrrrrr", "_B": "NEW: 32-char = 2-bar grid; r = 32nd ratchet (terminal buzz)"},
    "_note": "NEW drum 'B' = bat chirp (FM down-sweep 4→1.5 kHz, 18 ms). 8ths → 16ths → 32nd 'terminal buzz' (real bats: up to ~200 calls/s)."},
   {"name": "mantis12", "level_db": -1.5, "beats": 10,  "energy": 2.6, "scale": "chromatic",
    "progression": [["D3", "D#3", "E3", "F3", "F#3", "G3", "G#3", "A3", "A#3", "B3", "C4", "C#4"]], "chord_bars": 4,
    "voices": ["prizma", "goz", "bass", "pad"], "drums": {"K": "X.......X.......", "H": "x.x.x.x.x.x.x.x.", "S": "....X.......X..."}},
   {"name": "mantis_kaba", "level_db": -2.5, "beats": 7, "energy": 1.3, "scale": "major", "progression": [["D2", "D3"]], "riser": True, "riser_kind": "noise",
    "voices": ["bass", "pad"], "drums": "none", "_note": "the cluster collapses to a bare octave on the twist word 'Ama'"},
   {"name": "dusus",    "level_db": 1.5, "beats": 8,  "energy": 3.2, "scale": "lydian", "drop": True, "progression": [["D3", "F#3", "A3", "C#4"], ["E3", "G#3", "B3", "D4"]],
    "chord_bars": 1, "voices": ["goz", "vizilti", "kuyruk", "sonar", "prizma", "bass", "pad"],
    "drums": {"K": "X...x...X...x...", "S": "....X.......X...", "H": "x.x.x.x.x.x.x.x.", "B": "...x.......x...."}},
   {"name": "nagel",    "level_db": -4.0, "beats": 12, "energy": 1.4, "scale": "major", "progression": [["D3", "F#3", "A3"], ["B2", "D3", "F#3"]], "chord_bars": 2,
    "voices": ["sonar", "pad", "bass"], "drums": {"K": "X...............", "B": "x..............."}},
   {"name": "dongu",    "level_db": -1.0, "beats": 3,  "energy": 1.6, "scale": "major", "progression": [["D3", "F#3", "A3"]], "voices": ["goz", "bass", "pad"],
    "drums": {"K": "X.......X.......", "H": "..x...x...x...x.", "S": "....o.......o..."}, "_note": "same groove as frame 0 (seamless loop)"}],
  "logo": {"at": ["reveal", "loop"], "voice": "goz"},
  "sfx": {"tick": None}},
 "brand": {"handle": "@hayret.piksel", "auto": False},
 "loop": True, "loop_beats": 1, "loop_transition": {"type": "dissolve", "beats": 1},
 "segments": [
  seg(id="S1", role="hook", scene="vision_world", beats=8, vision="insan",
      params={"time": "day", "focus": "flower", "bee_path": "approach", "peek": {"at": 5.0, "beats": 0.75, "mode": "ari"}},
      layers=DAY_L, camera={"zoom": [1.25, 1.45], "pan": [[0, 6], [2, 18]], "ease": "inOutSine"},
      transition_in="cut",
      narration=[{"text": "Aynı çiçek. Bir *arı* ne görüyor?", "at": 0, "place": "top", "size": "head", "reveal": "word", "rate": "16th"}],
      events=[{"at": 5.0, "kind": "pulse", "label": "PEEK: 0,75 vuruşluk arı-görüşü göz kırpması (morötesi hedef bir anlığına görünür)"},
              {"at": 6.0, "kind": "mark", "label": "arı çiçeğe yaklaşır"}]),
  seg(id="S2", role="rehook", scene="vision_world", beats=10, vision="ari",
      params={"time": "day", "focus": "flower", "bee_path": "land", "uv_glow": True},
      layers=DAY_L, camera={"zoom": [1.45, 1.6], "pan": [[2, 18], [2, 22]], "ease": "inOutSine"},
      transition_in={"type": "iris", "beats": 1.5, "_note": "hayret-eye iris = the eye opens INTO the new vision, same scene & camera continue"},
      subject=[-22, -2, 26, 46],
      narration=[{"text": "Arılar *morötesini* görür: çiçekte gizli bir hedef belirir.", "at": 0.5, "place": "top"},
                 {"text": "UV deseni", "at": 5, "place": "callout", "target": [2, 42], "side": "below", "reveal": "word", "rate": "8th",
                  "_note": "render: points at the lower petal tip (UV ring) from below so the box never covers the bullseye"}],
      events=[{"at": 0, "kind": "rehook", "label": "dünya renk değiştirir: morötesi"}, {"at": 5, "kind": "pop", "label": "boğa gözü deseni parlar"}]),
  seg(id="S3", role="step", scene="vision_world", beats=10, vision="kopek",
      params={"time": "day", "focus": "ball", "dog": True, "pixel": 2, "peek": {"at": 5.0, "beats": 1.25, "mode": "insan"}},
      layers=DAY_L, camera={"zoom": [1.35, 1.45], "pan": [[-44, 64], [-48, 70]], "ease": "inOutSine"},
      subject=[-60, 64, -36, 88],
      transition_in={"type": "match", "_note": "match from flower centre to ball (both round)"},
      narration=[{"text": "Köpekte iki tür koni var: kırmızı top çimde _kaybolur_.", "at": 0, "place": "top"}],
      events=[{"at": 0, "kind": "rehook", "label": "yeni göz: köpek"}, {"at": 5, "kind": "pop", "label": "top çime karışır (yan yana insan/köpek ayrımı 1 vuruş)"}]),
  seg(id="S4", role="step", scene="vision_world", beats=10, vision="yilan",
      params={"time": "dusk", "focus": "mouse", "snake": True, "heat_blur": 2.0},
      layers=NIGHT_L, camera={"zoom": [1.3, 1.42], "pan": [[56, 68], [58, 74]], "ease": "inOutSine"},
      transition_in={"type": "dissolve", "beats": 1.5},
      narration=[{"text": "Yılanın yüzündeki çukurlar *ısıyı* algılar: fare karanlıkta parlar.", "at": 0.5, "place": "mid"}],
      subject=[48, 68, 74, 86],
      events=[{"at": 0, "kind": "rehook", "label": "yeni göz: ısı"}, {"at": 4, "kind": "pulse", "label": "farenin ısı izi nabız gibi atar"}]),
  seg(id="S5", role="rehook", scene="vision_world", beats=10, vision="yarasa",
      params={"time": "night", "focus": "bat", "sonar": {"origin": "bat", "rings_on": "drum:B", "persistence_beats": 1.5}},
      layers=NIGHT_L, camera={"zoom": [1.15, 1.2], "pan": [[8, -14], [12, -18]], "ease": "inOutSine",
              "_note": "render: widened so the hive label (moved to (50, 6)) and the bat are both in view"},
      subject=[-54, -60, -38, -44],
      transition_in={"type": "crt", "floor": 0.6, "_note": "render: floor keeps a dim after-image (QC: no near-black frames); light switches off → the world exists only where echoes return"},
      props=[{**HIVE_LABEL, "from": 1.0, "legible": False,
              "_note": "SUBTLE tag: hive label drawn only as sonar contours when a ring passes"}],
      narration=[{"text": "Yarasa ise *sesle* görür: bağırır, yankıdan dünyayı çizer.", "at": 0.5, "place": "panel"}],
      events=[{"at": 0, "kind": "rehook", "label": "karanlık + tık sesleri"}, {"at": 8, "kind": "mark", "label": "beslenme vızıltısı: tıklar hızlanır"}]),
  seg(id="S6", role="rehook", scene="vision_world", beats=10, vision="mantis12",
      params={"time": "day", "focus": "shrimp", "underwater": True},
      layers=DAY_L,
      camera={"zoom": [1.5, 1.62], "pan": [[2, 112], [0, 116]], "ease": "inOutSine"},
      transition_in={"type": "tiles", "_note": "Çini tiles flip into the 12-band world"},
      subject=[-20, 122, 26, 136],
      narration=[{"text": "Mantis karidesinde *12* renk alıcısı var; bizde sadece 3.", "at": 0.5, "place": "top", "size": "body"}],
      events=[{"at": 0, "kind": "rehook", "label": "sayı: 12 alıcı"}]),
  seg(id="S7", role="twist", scene="vision_world", beats=7, vision="mantis_kaba",
      params={"time": "day", "focus": "shrimp", "underwater": True, "collapse": {"from": "mantis12", "beats": 1.0}},
      layers=DAY_L,
      camera={"zoom": [1.62, 1.68], "pan": [[0, 116], [0, 118]], "ease": "inOutSine"},
      transition_in={"type": "glitch", "_note": "the 12 bands snap to 5 flat classes; fast-transition budget spent on the twist"},
      subject=[-20, 122, 26, 136],
      narration=[{"text": "Ama renkleri bizden _kötü_ ayırt ediyor!", "at": 0, "place": "mid", "size": "head"}],
      events=[{"at": 0, "kind": "twist", "label": "12 alıcı ≠ iyi renk görüşü (Thoen 2014)"}]),
  seg(id="S8", role="reveal", scene="vision_mosaic", beats=8,
      params={"tiles": ["insan", "ari", "kopek", "yilan", "yarasa", "mantis12"], "grid": [2, 3], "crop": [-44, -36, 46, 69], "stagger_beats": 0.25},
      layers={"back": ["tiles", "rays"], "front": ["dust", "bokeh"]},
      camera={"zoom": [1.0, 1.06], "ease": "inOutSine"},
      transition_in={"type": "mosaic", "_note": "literal: the frame breaks into 6 eye-tiles on the drop"},
      narration=[{"text": "Altı göz, tek dünya: hepsi birer _çeviri_.", "at": 0, "place": "top", "size": "head", "xy": [0.5, 0.335]}],
      events=[{"at": 0, "kind": "reveal", "label": "drop + sonic logo; 6 göz yan yana"}]),
  seg(id="S9", role="payoff", scene="vision_world", beats=12, vision="hayret",
      params={"time": "night", "focus": "bat_hive", "bat_close": True, "hive_label": "@hayret.piksel"},
      layers=NIGHT_L, camera={"zoom": [1.1, 1.15], "pan": [[16, -8], [16, -12]], "ease": "inOutSine",
              "_note": "render: bat (left) + hive label (right) both in the safe area, label above the NAGEL dialog"},
      subject=[-54, -60, -38, -44],
      transition_in={"type": "silhouette", "shape": "assets/bat_shape.png", "_note": "morph through the bat silhouette into the brand night"},
      props=[{**HIVE_LABEL, "from": 0.5, "legible": True,
              "_note": "LEGIBLE tag: painted label on the beehive (target: hive_label surface)"}],
      narration=[{"text": "Bir yarasa olmak *nasıl bir şey*? Yankıyı çizebiliriz; hissini bilemeyiz.", "at": 0.5,
                  "place": "dialog", "speaker": "NAGEL, 1974"}],
      events=[{"at": 6, "kind": "mark", "label": "yarasa başını çevirip kameraya bakar (göz logosu yansıması)"}]),
  seg(id="S10", role="loop", scene="vision_world", beats=3, vision="insan",
      params={"time": "day", "focus": "flower", "bee_path": "approach"},
      layers=DAY_L, layer_sync="loop", camera={"zoom": [1.2, 1.25], "pan": [[0, 6], [0, 6]], "ease": "outCubic"},
      transition_in={"type": "dissolve", "beats": 1.5, "_note": "sunrise back to the hook frame; last frame == frame 0"}),
 ]}

json.dump(spec, open("spec.json", "w"), ensure_ascii=False, indent=2)

# ---------------- proxy: existing scenes only (image scene shows the mock vision stills), union palette
px = copy.deepcopy(spec)
px["palette"] = union_palette("insan"); px.pop("visions")
IMG = {"insan": "assets/vis_insan.png", "ari": "assets/vis_ari.png", "kopek": "assets/vis_kopek.png", "yilan": "assets/vis_yilan.png",
       "yarasa": "assets/vis_yarasa_1.png", "mantis12": "assets/vis_mantis12.png", "mantis_kaba": "assets/vis_mantis_kaba.png",
       "hayret": "assets/vis_night.png"}
for g in px["segments"]:
    v = g.pop("vision", None)
    img = "assets/vis_mosaic.png" if g["scene"] == "vision_mosaic" else IMG[v]
    g["scene"] = "image"; g["params"] = {"image": img, "height": 320, "glow": 0.0, "float": 0.6}
    tr = g["transition_in"]
    if isinstance(tr, dict): g["transition_in"] = {k: v for k, v in tr.items() if not k.startswith("_")}
    for p in g.get("props", []): p.pop("_note", None)
m = px["music"]
for v in m["voices"].values():
    if v: v.pop("max_notes", None)
for s in m["sections"]:
    if isinstance(s.get("drums"), dict):
        d = {k: v for k, v in s["drums"].items() if not k.startswith("_")}
        if "B" in d: d["R"] = d.pop("B")[:16]     # proxy: rim stands in for the bat chirp, 1-bar grid
        s["drums"] = d
    for k in [k for k in s if k.startswith("_")]: s.pop(k)
json.dump(px, open("spec_proxy.json", "w"), ensure_ascii=False, indent=2)
print("ok", sum(g["beats"] for g in spec["segments"]), "beats =", round(sum(g["beats"] for g in spec["segments"]) * 60 / BPM, 2), "s")
