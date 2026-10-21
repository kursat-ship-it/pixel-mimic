"""gelecek-secim: writes spec.json (target: NEW scenes + list-series music) and spec_proxy.json
(same timeline, existing scenes/features only) for validate / sheet / music smoke test.
Edit THIS file, then: python build_spec.py (repo venv active)"""
import json, copy
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # outputs land next to this file

# ---- the PROPHECY melody (scale degrees of E harmonic minor, one per 8th note, 2 bars of 4/4 = 16 notes)
#      E G B G | E B E' B | C B G B | F# D# D# E      → the book "predicts" the final E (index 15)
KEHANET = [0, 2, 4, 2, 0, 4, 7, 4, 5, 4, 2, 4, 1, -1, -1, 0]
# ---- the AVOIDER melody (7/8 = 2+2+3, 14 eighths = 2 bars). Same opening, but the bar is one 8th SHORT and the
#      7th note is C (degree 5) where the prophecy says high E (degree 7): the dodge lands on S6 beat 3 = the hero's turn.
#      Bar 2 is a new line the book never wrote.
KACIS = [0, 2, 4, 2, 0, 4, 5, 4, 2, 0, 2, 4, 5, 7]

CAP = 12
def chk(t):
    for l in t.replace("*", "").split("\n"):
        assert len(l) <= CAP, (l, len(l))
    return t

def seg(**k):
    for c in ([k["caption"]] if "caption" in k else []) + k.get("captions", []):
        chk(c["text"])
    return k

L_BOOK = {"back": ["stars", "nebula", "skyline"], "front": ["dust", "bokeh"]}
L_CLOCK = {"back": ["tiles", "rays", "stars"], "front": ["dust", "debris"]}

spec = {
 "version": 2, "preset": "hayret", "pacing": "punchy",   # pinned: rendered before the calm default (Oct 2026)
 "meta": {
  "title": "Geleceğini Bilseydin, Yine Seçebilir miydin? 🎧",
  "description": "Laplace 1814'te her şeyi bilen bir zihnin geleceği geçmiş kadar net göreceğini yazdı. Ama sana söylenen bir kehanet, onu duyan seni de değiştirir: Scriven (1965) 'tersini yaparım' diyen birinin kendisine söylenen tahmini bozabileceğini savundu (tartışmalı), MacKay (1960) ise kehanetin ancak senden gizli kalırsa tutabileceğini. Libet'in 1983 deneyi ise 2012'de 'beyin gürültüsü' ile yeniden yorumlandı. PhilPapers 2020 anketine yanıt veren filozofların %59'u özgür iradenin determinizmle bağdaştığını (uyumculuk) kabul ediyor ya da ona yakın duruyor. Sen olsan kitabı okur muydun? 👇",
  "hashtags": ["#felsefe", "#özgürirade", "#bilim", "#pixelart", "#chiptune", "#hayretpiksel"],
  "lang": "tr", "cover_t": 1.0},
 "format": {"width": 1080, "height": 1920, "fps": 30, "grid": 6},
 "music": {
  "_concept": "Clockwork vs. choice. 4/4 sections are a ticking music-box clock that plays the PROPHECY melody (KEHANET); a quiet 'whisper' voice plays every prophecy note one 8th EARLY (you hear the future before it happens). At the twist the meter loses an 8th (4/4 → 7/8) and the AVOIDER melody (KACIS) dodges the predicted final E onto C while the whisper still predicts E: the prediction audibly fails. The drop stays in 7/8 and opens to E dorian (the 'avoided' note becomes a bright C#). Back to the clock for the answer; the loop seam lands on the sonic logo's 3rd (G) where the whisper predicted E — a last fake-out.",
  "bpm": 120, "meter": "4/4", "key": "E", "scale": "harmonic_minor", "tuning": "12tet", "flavour": "fm",
  "progression": ["i", "i", "VI", "V7"], "chord_bars": 0.5, "swing": 0, "seed": 1814,
  "hf_shelf_db": -3.0,
  "series_defs": {"kehanet": {"values": KEHANET, "period": 16}, "kacis": {"values": KACIS, "period": 14}},
  "voices": {
   "saat":    {"role": "lead", "type": "fm", "ratio": 3.5, "index": 2.2, "idecay": 9, "octave": 5, "vol": 0.075, "pan": 0.1,
               "env": {"a": 0.002, "d": 0.25, "s": 0.15, "r": 0.15},
               "series": {"name": "kehanet", "rate": 2, "phase": "global"},
               "_note": "music-box / clock-chime bell playing the prophecy"},
   "fisilti": {"role": "counter", "type": "pulse", "duty": 0.125, "octave": 6, "vol": 0.022, "pan": -0.35,
               "env": {"a": 0.001, "d": 0.05, "s": 0.0, "r": 0.02},
               "series": {"name": "kehanet", "rate": 2, "phase": "global", "lookahead": 1, "logo_duck": 0.5},
               "_note": "the whisper: plays kehanet[n+1] at slot n = every note one 8th early. Keeps predicting KEHANET even in 7/8"},
   "fisilti_k": {"role": "counter", "type": "pulse", "duty": 0.25, "octave": 5, "vol": 0.05, "pan": -0.3,
               "env": {"a": 0.001, "d": 0.09, "s": 0.0, "r": 0.03},
               "series": {"name": "kehanet", "rate": 2, "phase": "global", "lookahead": 1},
               "_note": "QC: S6-only whisper, same register as the dodge so 'E predicted → C played' is audible (the S1–S5 whisper sits ~30 dB under the lead's fundamental)"},
   "kacis":   {"role": "lead", "type": "pulse", "duty": 0.25, "pwm": 0.12, "octave": 5, "vol": 0.07, "pan": 0.1, "vibrato": 0.1, "vib_delay": 0.15,
               "env": {"a": 0.003, "d": 0.18, "s": 0.45, "r": 0.06},
               "series": {"name": "kacis", "rate": 2, "phase": "section"},
               "_note": "the avoider melody, 7/8 sections only"},
   "carklar": {"role": "arp", "type": "fm", "ratio": 2.0, "index": 1.0, "idecay": 14, "octave": 5, "vol": 0.028,
               "pattern": "up", "rate": 4, "pan": -0.15, "min_energy": 2.0, "_note": "gear-tooth 16ths"},
   "bass":    {"role": "bass", "type": "pulse", "duty": 0.5, "octave": 3, "vol": 0.07, "pattern": "octave", "rate": 2,
               "filter": "soft", "_note": "pulse not triangle so phone speakers keep the bass line (QC lesson); octave 3, no sub"},
   "pad":     {"role": "pad", "type": "saw", "octave": 4, "vol": 0.022, "min_energy": 2.8, "filter": "soft"},
   "lead": None, "counter": None, "arp": None},
  "drums": {"K": "X.......X.......", "R": "X...x...X...x...", "T": "..x...x...x...x.", "H": "....o.......o..."},
  "sections": [
   {"name": "kehanet",  "beats": 8,  "energy": 1.8, "voices": ["saat", "fisilti", "bass"]},
   {"name": "laplace",  "beats": 8,  "energy": 2.0, "voices": ["saat", "fisilti", "bass", "carklar"]},
   {"name": "saat",     "beats": 8,  "energy": 2.2, "voices": ["saat", "fisilti", "bass", "carklar"],
    "drums": {"K": "X.......X.......", "R": "X...x...X...x...", "T": "..x...x...x...x.", "S": "....X.......X..."}},
   {"name": "kamplar",  "beats": 8,  "energy": 2.3, "voices": ["saat", "fisilti", "bass", "carklar"], "fill": True,
    "drums": {"K": "X.......X.......", "R": "X...x...X...x...", "T": "..x...x...x...x.", "S": "....X.......X..."}},
   {"name": "libet",    "beats": 8,  "energy": 1.6, "voices": ["saat", "bass"],
    "drums": {"R": "X...............", "K": "X.......x......."}, "_note": "almost bare: one tick per bar, like the Libet clock"},
   {"name": "kacis",    "beats": 7,  "energy": 2.0, "meter": "7/8", "grouping": [2, 2, 3], "progression": ["i", "VI"], "chord_bars": 1,
    "voices": ["kacis", "fisilti_k", "bass"], "drums": "aksak_7_8"},
   {"name": "zar",      "beats": 7,  "energy": 1.6, "meter": "7/8", "grouping": [2, 2, 3], "progression": ["i", "VI"], "chord_bars": 1,
    "riser": True, "riser_kind": "noise", "stop": 0.5, "voices": ["carklar", "bass"]},
   {"name": "dusus",    "beats": 14, "energy": 3.0, "meter": "7/8", "grouping": [2, 2, 3], "drop": True, "scale": "dorian",
    "progression": ["i", "IV", "i", "VII"], "chord_bars": 1, "voices": ["kacis", "carklar", "bass", "pad"],
    "drums": {"K": "X...X...X.....", "S": "....X.......X.", "H": "x.x.x.x.x.x.x.", "T": "..x...x...x.x."}},
   {"name": "cevap",    "beats": 8,  "energy": 2.4, "meter": "4/4", "scale": "harmonic_minor", "progression": ["i", "i", "iv", "VI"],
    "chord_bars": 0.5, "voices": ["saat", "fisilti", "bass", "carklar"]},
   {"name": "dongu",    "beats": 4,  "energy": 1.8, "meter": "4/4", "voices": ["saat", "fisilti", "bass"]}
  ],
  "logo": {"at": ["reveal", "loop"], "voice": "saat"},
  "sfx": {"tick": "tick"}},
 "brand": {"handle": "@hayret.piksel", "auto": False},
 "fx": {"flash": 0.3},   # (render: hit-flash 0.55→0.3 — QC: "flash too white"; the drop frame stays readable)
 "loop": True, "loop_beats": 1, "loop_transition": {"type": "dissolve", "beats": 1},
 "segments": [
  seg(id="S1", role="hook", scene="future_book", beats=8,
      params={"mode": "read", "arrow": "left", "page_flip_every": 0.5, "fork": True, "roll": True, "roll_series": "kehanet",
              "step_at": 3, "sprite_scale": 2.4},
      layers=L_BOOK, camera={"zoom": [1.0, 1.35], "pan": [[0, 0], [-6, -10]], "orbit": 2, "ease": "inCubic"},
      transition_in="cut",
      caption={"text": "GELECEĞİN\nYAZILIYSA\n*SEÇEN KİM?*", "at": [0, 4.5]},
      # (render: no pulse at beat 0 — frame 0 must equal the loop's last frame; sprite_scale 2→2.4 for phone readability)
      events=[{"at": 1.5, "kind": "punch", "label": "kitaptaki ok SOLU gösterir"},
              {"at": 3, "kind": "pop", "label": "karakter sola adım atar (tam kehanet gibi)"}, {"at": 5, "kind": "punch", "label": "kitabın okuna crash zoom başlar"}]),
  seg(id="S2", role="rehook", scene="laplace_demon", beats=8,
      params={"balls": 7, "paths": True, "eyes": 9, "path_reveal_every": 1, "abacus": True},
      layers={"back": ["stars", "nebula", "rays"], "front": ["dust", "bokeh"]},
      camera={"zoom": [1.5, 1.0], "ease": "outCubic"},
      transition_in={"type": "crash", "beats": 1.0},
      captions=[{"text": "*1814*:\nLAPLACE'IN\nŞEYTANI", "at": [0.5, 3.5]},
                {"text": "GELECEĞİ\nGEÇMİŞ GİBİ\nGÖRÜR", "at": [4.2, 7.0]}],
      events=[{"at": 0, "kind": "rehook", "label": "yeni karakter: şeytan + 1814"}, {"at": 2, "kind": "pulse"},
              {"at": 4, "kind": "punch", "label": "bilardo topları kesik çizgili geleceklerine tam oturur"}, {"at": 6, "kind": "pulse"}]),
  seg(id="S3", role="step", scene="dominoes", beats=8,
      params={"n": 24, "fall_every": 0.5, "clock": True, "pendulum": True, "perspective": True},
      layers=L_CLOCK, camera={"zoom": [1.0, 1.06], "pan": [[0, 18], [-2, 22]], "ease": "inOutSine"},  # QC: was pan ±30 / zoom 1.2: hero off-frame for ~0.7 s, plate cut at the right edge, hero in the bottom UI zone
      transition_in={"type": "whip", "beats": 0.5, "dir": "right"},
      props=[{"kind": "plate", "x": 30, "y": 17, "s": 0.8, "layer": "mid", "par": 1.0, "from": 1.0, "legible": False, "model": "LAPLACE-1814"}],
      caption={"text": "EVREN BİR\nSAAT GİBİ\nİŞLİYORSA...", "at": [0.5, 4.0]},
      events=[{"at": 2, "kind": "punch"}, {"at": 4, "kind": "rehook", "label": "zincir karakterimize doğru geliyor: o da domino mu?"}, {"at": 6, "kind": "punch", "label": "son domino bizim karaktere yaklaşır"}]),
  seg(id="S4", role="contrast", scene="dominoes", beats=8,
      params={"n": 16, "fall_every": 0.5, "split": True, "top": "hard", "bottom": "thinker", "thinker_at": 3},
      layers=L_CLOCK, camera={"zoom": [1.0, 1.08], "ease": "inOutSine"},
      transition_in={"type": "split", "beats": 2.0},
      captions=[{"text": "1. KAMP:\nSEÇİM BİR\n*YANILSAMA*", "at": [0.5, 3.5]},
                {"text": "2. KAMP:\nSEÇEN YİNE\n*SENSİN*", "at": [4.2, 7.2]}],
      events=[{"at": 0, "kind": "rehook", "label": "iki kamp, bölünmüş ekran"}, {"at": 3, "kind": "pop", "label": "alttaki domino gözünü açar, düşünür"},
              {"at": 4, "kind": "punch"}, {"at": 6, "kind": "pulse"}]),
  seg(id="S5", role="step", scene="libet_clock", beats=8,
      params={"period_s": 2.56, "rp_onset_ms": -550, "w_ms": -200, "press_at": 3, "noise_trials": 12, "noise_at": 4},
      layers={"back": ["grid", "horizon", "stars"], "front": ["dust", "debris"]},
      camera={"zoom": [1.2, 1.0], "ease": "outCubic"},
      transition_in={"type": "glitch", "beats": 0.5},
      props=[{"kind": "terminal", "x": 32, "y": 130, "s": 0.8, "layer": "mid", "par": 1.0, "from": 1.0, "legible": False, "start": 0.5, "lines": ["> @hayret.piksel", "> W = -200 ms"]}],
      captions=[{"text": "BEYNİN\nÖNCE Mİ\nKARAR VERİR?", "at": [0.3, 3.3]},
                {"text": "*1983*: EVET?\n*2012*: BELKİ\nGÜRÜLTÜ", "at": [4.2, 7.2]}],
      events=[{"at": 0, "kind": "rehook", "label": "yeni soru: beyin önden mi gidiyor"}, {"at": 3, "kind": "punch", "label": "düğmeye basılır; EEG rampası"},
              {"at": 4, "kind": "rehook", "label": "rampa = gürültü denemelerinin ortalaması (Schurger)"}, {"at": 6, "kind": "pulse"}]),
  seg(id="S6", role="twist", scene="future_book", beats=7,
      params={"mode": "avoid", "arrow": "left", "turn_at": 3.0, "fork": True, "roll": True, "roll_series": "kehanet",
              "actual_series": "kacis", "ink_crack_at": 3.0, "sprite_scale": 2.4},
      layers=L_BOOK, camera={"zoom": [1.25, 1.0], "ease": "outCubic"},
      transition_in={"type": "iris", "beats": 1.0},
      captions=[{"text": "AMA KEHANET\nSANA\nSÖYLENİRSE?", "at": [0, 2.5]},
                {"text": "*TERSİNİ*\nYAPABİLİRSİN", "at": [3.0, 6.0]}],
      events=[{"at": 0, "kind": "twist", "label": "4/4 → 7/8: saat bir sekizlik kaybeder"},
              {"at": 3, "kind": "punch", "sfx": "glitch", "label": "karakter SAĞA döner, kitaptaki ok çatlar; tahmin edilen nota (Mi) kaçırılır"},
              {"at": 5, "kind": "pulse"}]),
  seg(id="S7", role="build", scene="future_tree", beats=7,
      params={"mode": "dice", "dice": 2, "roll_every": 0.5, "branch_from_faces": True, "ring_countdown_from": 3.5},
      layers={"back": ["stars", "nebula", "rays"], "front": ["dust", "bokeh"]},
      camera={"zoom": [1.0, 1.3], "rot": [0, 20], "ease": "inCubic"},
      transition_in={"type": "spin", "beats": 1.0, "over": True},
      caption={"text": "KUANTUM ZARI\nKURTARIR MI?", "at": [0.3, 3.3]},
      events=[{"at": 2, "kind": "punch"}, {"at": 4, "kind": "rehook", "label": "sözsüz gerilim, halka daralır"}, {"at": 5.5, "kind": "pulse"}]),
  seg(id="S8", role="drop", scene="future_tree", beats=14,
      params={"mode": "burst", "depth": 6, "grow_every": 0.5, "walkers": 8, "chosen_path_glow": True, "pull_out": True},
      layers={"back": ["stars", "nebula", {"kind": "horizon", "k": 0.55}], "front": ["debris", "dust"]},
      camera={"zoom": [2.2, 0.8], "pan": [[0, 0], [0, 18]], "ease": "outCubic"},  # QC: horizon k .55 + lift 18
      transition_in={"type": "mosaic", "beats": 0.75},
      captions=[{"text": "SÖYLENEN\nKEHANET\n*ŞAŞABİLİR*", "at": [3.5, 7.0]},
                {"text": "GİZLİ\nKEHANET İSE\n*TUTABİLİR*", "at": [8.5, 12.5]}],
      events=[{"at": 0, "kind": "shake"}, {"at": 1.75, "kind": "pulse"}, {"at": 3.5, "kind": "rehook", "label": "Scriven: söylenen kehanet"},
              {"at": 7, "kind": "punch"}, {"at": 8.5, "kind": "rehook", "label": "MacKay: gizli kehanet"}, {"at": 10.5, "kind": "punch"},
              {"at": 12.25, "kind": "pulse"}]),
  seg(id="S9", role="reveal", scene="object", beats=8,
      params={"kind": "book", "state": "closing", "close_at": 0.5, "title": "GELECEĞİN\nKİTABI", "brand": "@hayret.piksel",
              "brand_at": 1.0, "reveal": 1.0, "candle": True, "desk": True},
      layers={"back": ["tiles", "rays", "stars"], "front": ["bokeh", "dust"]},
      camera={"zoom": [1.5, 1.0], "ease": "outCubic"},
      transition_in={"type": "tiles", "beats": 1.0},
      captions=[{"text": "FİLOZOFLARIN\n*%59*'U: SEÇİM\nYİNE VAR", "at": [0.5, 3.5]},
                {"text": "BİLMEK,\nSEÇMEYİ\n*SİLMEZ*", "at": [4.2, 7.2]}],
      events=[{"at": 0, "kind": "reveal", "label": "kitap kapanır: kapakta @hayret.piksel + ses logosu"}, {"at": 2, "kind": "pulse"},
              {"at": 4, "kind": "punch"}, {"at": 6, "kind": "pulse"}]),
  seg(id="S10", role="loop", scene="future_book", beats=4,
      params={"mode": "open", "open_from_cover": True, "converge_to_frame0": True, "fork": True, "roll": True, "roll_series": "kehanet",
              "sprite_scale": 2.4},
      # (render: camera starts ON the small cover at the size/position of S9's big cover so the match cut lands
      #  shape-on-shape — 120/26 = 4.615×, cover centre (14, 70) at screen y +6 — then pulls out to S1's frame 0)
      layers=L_BOOK, camera={"zoom": [4.615, 1.0], "pan": [[14, 68.7], [0, 0]], "ease": "outCubic"},  # QC: inOutCubic lingered ~0.5 s at 4.6x
      transition_in={"type": "match", "beats": 0.75}, layer_sync="first",
      events=[{"at": 1, "kind": "punch", "label": "kitap yeniden açılır"}, {"at": 2.5, "kind": "pulse"}]),
 ]
}
json.dump(spec, open("spec.json", "w"), ensure_ascii=False, indent=2)

# ---------------- proxy: existing scenes + existing music features only (timing/caption/retention board + music smoke test)
MAP = {"future_book": ("hero", {"branches": 5, "trace": True}), "laplace_demon": ("network", {}),
       "dominoes": ("chain", {}), "libet_clock": ("noise_scope", {"traces": ["pink"], "focus_trace": "pink", "label_1975": False}),
       "future_tree": ("junction", {})}
px = copy.deepcopy(spec)
for g in px["segments"]:
    if g["scene"] in MAP:
        g["_target_scene"] = g["scene"]; g["scene"], g["params"] = MAP[g["scene"]][0], dict(MAP[g["scene"]][1])
    elif g["scene"] == "object":
        g["_target_params"] = g["params"]; g["params"] = {"kind": "jar", "inner": "star", "brand": "@hayret.piksel", "brand_at": 1.0, "reveal": 1.0}
m = px["music"]; m.pop("series_defs")
for v in m["voices"].values():
    if v: v.pop("series", None)
m["voices"]["saat"]["role"] = "lead"; m["voices"]["fisilti"] = None; m["voices"]["fisilti_k"] = None; m["voices"]["kacis"] = None
m["motif"] = {"notes": KEHANET, "rhythm": [0.5]}
for s in m["sections"]:
    if s.get("voices"): s["voices"] = [x for x in s["voices"] if x not in ("fisilti", "fisilti_k", "kacis")] or ["saat"]
    if "kacis" in s["name"] or s["name"] == "dusus": s["voices"] = ["saat"] + [x for x in s["voices"] if x != "saat"]
json.dump(px, open("spec_proxy.json", "w"), ensure_ascii=False, indent=2)
print("ok", sum(g["beats"] for g in spec["segments"]), "beats")
