"""Writes spec.json (target, uses NEW scenes) and spec_proxy.json (same timeline, existing scenes) for validate/sheet."""
import json, copy
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # outputs land next to this file
def norgard(n):
    a = [0] * n
    for i in range(1, n): a[i] = -a[i // 2] if i % 2 == 0 else a[i // 2] + 1
    return a
A = norgard(64)

spec = {
 "version": 2, "preset": "hayret", "pacing": "punchy",   # pinned: rendered before the calm default (Oct 2026)
 "meta": {
  "title": "Bu Melodinin İçinde Kendisi Saklı 🎧",
  "description": "Bu melodinin her 4. notasını alırsan yine aynı melodiyi duyarsın. 🎧 Danimarkalı besteci Per Nørgård 1959'da bu 'sonsuzluk serisi'ni buldu: her 4. nota serinin kendisini, her 2. nota ters çevrilmiş hâlini veriyor. Voss & Clarke (1975) ise müzikteki gürlük ve perde dalgalanmalarının fraktal benzeri 1/f ('pembe gürültü') yasasına uyduğunu gösterdi. Bu videodaki melodi ve bas baştan sona o seriden üretildi: 4 kanal, 4 hız, tek melodi. Sence müzik gizli bir matematik mi? 👇",
  "hashtags": ["#fraktal", "#matematik", "#müzik", "#pixelart", "#chiptune", "#hayretpiksel"],
  "lang": "tr", "cover_t": 1.2},
 "format": {"width": 1080, "height": 1920, "fps": 30, "grid": 6},
 "music": {
  "bpm": 100, "meter": "4/4", "key": "G", "scale": "dorian", "tuning": "12tet", "flavour": "2a03",
  "progression": ["i"], "chord_bars": 4, "swing": 0, "seed": 1959,
  "_concept": "The whole score is ONE melody: Nørgård's infinity series a(0)=0, a(2n)=-a(n), a(2n+1)=a(n)+1, mapped onto scale degrees from G. Four NES-style channels play it at four speeds (16ths, 8ths inverted, quarters, whole notes). Because a(4n)=a(n) and a(2n)=-a(n), the slow voices always land in unison/octave with the fast one: the soundtrack is literally self-similar. Progression is a static i (G drone) so the series supplies all melodic motion.",
  "voices": {
   "lead":    {"role": "lead", "type": "pulse", "duty": 0.125, "octave": 5, "vol": 0.06, "pan": 0.15, "echo": 0,
               "_echo_note": "echo off: a 0.75-beat echo of 16ths smeared a(n) over a(n+3)",
               "env": {"a": 0.002, "d": 0.08, "s": 0.35, "r": 0.03},
               "series": {"name": "norgard", "rate": 4, "sign": 1, "phase": "global"}},
   "counter": {"role": "counter", "type": "pulse", "duty": 0.5, "octave": 4, "vol": 0.045, "pan": -0.3, "pwm": 0.15,
               "env": {"a": 0.004, "d": 0.15, "s": 0.4, "r": 0.05},
               "series": {"name": "norgard", "rate": 2, "sign": -1, "phase": "global"}},
   "lead_q":  {"role": "lead", "type": "pulse", "duty": 0.25, "octave": 5, "vol": 0.07, "pan": 0.0, "vibrato": 0.12, "vib_delay": 0.2,
               "env": {"a": 0.004, "d": 0.2, "s": 0.55, "r": 0.08},
               "series": {"name": "norgard", "rate": 1, "sign": 1, "phase": "global"},
               "_note": "the 'proof' voice: series at quarter notes in the lead's register = every 4th lead note"},
   "bass":    {"role": "bass", "type": "triangle", "octave": 3, "vol": 0.12, "pattern": "sustain",
               "series": {"name": "norgard", "rate": 1, "sign": 1, "phase": "global"}},
   "sub":     {"role": "pad", "type": "wave", "table": "bass", "octave": 2, "vol": 0.05,
               "env": {"a": 0.05, "d": 0.6, "s": 0.7, "r": 0.4},
               "series": {"name": "norgard", "rate": 0.25, "sign": 1, "phase": "global"}},
   "arp":     None,
   "pad":     None},
  "drums": "breakbeat",
  "sections": [
   {"name": "tohum",    "beats": 6, "energy": 2.0, "drums": "half_time", "voices": ["lead"]},
   {"name": "ikinci_hiz","beats": 6, "energy": 2.0, "drums": "breakbeat", "voices": ["lead", "bass"]},
   {"name": "koch",     "beats": 6, "energy": 2.2, "voices": ["lead", "bass", "counter"]},
   {"name": "pembe",    "beats": 8, "energy": 2.3, "voices": ["lead", "bass", "counter"], "fill": True},
   {"name": "kanit_a",  "beats": 4, "energy": 1.0, "drums": "none", "voices": ["lead_q", "bass"]},
   {"name": "kanit_b",  "beats": 4, "energy": 2.0, "drums": "half_time", "voices": ["lead", "lead_q", "bass"]},
   {"name": "agac",     "beats": 6, "energy": 2.5, "drums": "breakbeat", "voices": ["lead", "counter", "bass", "sub"], "fill": True},
   {"name": "shepard",  "beats": 8, "energy": 1.5, "riser": True, "riser_kind": "shepard", "stop": 0.5, "voices": ["counter", "sub"]},
   {"name": "dusus",    "beats": 8, "energy": 3.0, "drop": True, "scale": "lydian", "drums": "four_on_floor",
    "voices": ["lead", "counter", "bass", "sub"]},
   {"name": "cevap",    "beats": 8, "energy": 2.5, "scale": "lydian", "drums": "breakbeat", "voices": ["lead", "counter", "bass", "sub"]},
   {"name": "dongu",    "beats": 6, "energy": 2.0, "scale": "dorian", "drums": "half_time", "voices": ["lead"]}
  ],
  "logo": {"at": ["reveal", "loop"]},
  "sfx": {"tick": "tick"}},
 "brand": {"handle": "@hayret.piksel", "auto": False},
 "loop": True, "loop_beats": 1,
 "loop_transition": {"type": "dissolve", "beats": 1},
 "segments": [
  {"id": "S1", "role": "hook", "scene": "fractal_staff", "beats": 6,
   "params": {"mode": "play", "series": "norgard", "rate": 4, "depth": 0, "playhead": True, "zoom_into_note": 24, "nest_preview": True, "keys": True,
              "_zoom_note": "series index 24 = the note on the playhead at beat 6, i.e. exactly when the crash cut lands"},
   "layers": {"back": ["horizon", "tiles", {"kind": "nebula", "ramps": ["dim", "energy", "body"]}, "stars"], "front": [{"kind": "bokeh", "ramps": ["pale", "energy"]}, "dust"]},
   "camera": {"zoom": [1.0, 1.7], "pan": [[0, 0], [18, -6]], "orbit": 2, "ease": "inCubic"},
   "transition_in": "cut",
   "caption": {"text": "BU MELODİNİN\nİÇİNDE\n*KENDİSİ* VAR!", "at": [0, 4.5]},
   "events": [{"at": 2, "kind": "punch"}, {"at": 4, "kind": "pop", "label": "nota içinde minik porte belirir"}],
   "_events_note": "no flash/pulse on beat 0: frame 0 must equal the loop's last frame"},
  {"id": "S2", "role": "rehook", "scene": "fractal_staff", "beats": 6,
   "params": {"mode": "nest", "series": "norgard", "rate": 4, "depth": 1, "show_parent_edge": True, "bass_staff": True},
   "layers": {"back": ["horizon", "tiles", {"kind": "nebula", "ramps": ["dim", "energy", "body"]}, "stars"], "front": [{"kind": "bokeh", "ramps": ["pale", "energy"]}, "dust"]},
   "camera": {"zoom": [2.4, 1.0], "ease": "outCubic"},
   "transition_in": {"type": "crash", "beats": 1.0},
   "caption": {"text": "YAKINLAŞ:\nAYNI MELODİ\n*TEKRAR*", "at": [1, 4.5]},
   "events": [{"at": 0, "kind": "rehook", "label": "notanın içinden aynı porte çıkıyor"}, {"at": 3, "kind": "punch"}]},
  {"id": "S3", "role": "promise", "scene": "koch", "beats": 6,
   "params": {"kind": "snowflake", "iter_from": 0, "iter_to": 4, "step_every": 1, "spark_notes": True, "inner_glow": True},
   "layers": {"back": ["rays", "nebula", "stars"], "front": ["dust", "bokeh"]},
   "camera": {"zoom": [1.0, 1.3], "rot": [0, 30], "ease": "inOutSine"},
   "transition_in": {"type": "whip", "beats": 0.5, "dir": "left"},
   "caption": {"text": "FRAKTALLARDA\nSONSUZ MÜZİK\nSAKLI MI?", "at": [0.5, 5]},
   "events": [{"at": 1, "kind": "pulse"}, {"at": 2, "kind": "pulse"}, {"at": 3, "kind": "punch"}, {"at": 4, "kind": "pulse"},
              {"at": 5, "kind": "rehook", "label": "soru + cevap sonda vaadi"}]},
  {"id": "S4", "role": "step", "scene": "noise_scope", "beats": 8,
   "params": {"traces": ["white", "pink", "brown"], "focus_trace": "pink", "focus_at": 3, "label_1975": True},
   "layers": {"back": ["grid", "horizon", "stars"], "front": ["dust", "debris"]},
   "camera": {"zoom": [1.15, 1.0], "pan": [[0, 20], [0, 0]], "ease": "outCubic"},
   "transition_in": {"type": "glitch", "beats": 0.5},
   "props": [{"kind": "terminal", "x": 30, "y": 112, "s": 0.8, "layer": "back", "par": 0.5, "from": 1.0, "legible": False,
              "lines": ["> @hayret.piksel", "> spektrum: 1/f"], "start": 1.6}],
   "captions": [{"text": "MÜZİK DE\nFRAKTAL GİBİ\nDALGALANIR", "at": [0.5, 3.5]},
                {"text": "*1/F* YASASI\nVOSS 1975", "at": [4.5, 7.3]}],
   "events": [{"at": 3, "kind": "punch", "label": "pembe iz türkuaz parlar"}, {"at": 4, "kind": "rehook", "label": "1/f sayısı"},
              {"at": 6, "kind": "pulse"}]},
  {"id": "S5", "role": "twist", "scene": "fractal_staff", "beats": 8,
   "params": {"mode": "every4", "series": "norgard", "rate": 4, "dim_others": True, "drop_to_bass_at": 2, "bass_staff": True},
   "layers": {"back": ["horizon", "tiles", {"kind": "nebula", "ramps": ["dim", "energy", "body"]}, "stars"], "front": [{"kind": "bokeh", "ramps": ["pale", "energy"]}, "dust"]},
   "camera": {"zoom": [1.0, 1.2], "ease": "inOutSine"},
   "transition_in": {"type": "crt", "beats": 1.0},
   "captions": [{"text": "AMA ASIL\nSIR ŞU:", "at": [0, 2]},
                {"text": "HER *4.* NOTA\n= AYNI\nMELODİ", "at": [2.5, 7]}],
   "events": [{"at": 0, "kind": "twist", "label": "her 4. nota yanar, diğerleri söner"}, {"at": 2, "kind": "pop"},
              {"at": 4, "kind": "punch", "label": "hızlı melodi geri gelir: ikisi üst üste"}, {"at": 6, "kind": "pulse"}]},
  {"id": "S6", "role": "number", "scene": "series_tree", "beats": 6,
   "params": {"levels": 5, "grow_every": 1, "leaves_play": True, "show_rule": True},
   "layers": {"back": ["rays", "nebula", "stars"], "front": ["dust", "bokeh"]},
   "camera": {"zoom": [1.4, 1.0], "pan": [[0, -40], [0, 0]], "ease": "outCubic"},
   "transition_in": {"type": "match", "beats": 0.75},
   "props": [{"kind": "chalkboard", "x": -34, "y": 116, "s": 0.8, "layer": "back", "par": 0.4, "from": 1.5, "legible": False,
              "lines": ["a(2n)=-a(n)", "a(2n+1)=a(n)+1"]}],
   "caption": {"text": "*1959*: BİR\nBESTECİ\nBUNU BULDU", "at": [0.5, 5]},
   "events": [{"at": 0, "kind": "rehook", "label": "yeni sayı: 1959"}, {"at": 2, "kind": "pulse"}, {"at": 3, "kind": "punch"}, {"at": 5, "kind": "pulse"}]},
  {"id": "S7", "role": "build", "scene": "shepard_stairs", "beats": 8,
   "params": {"steps": 12, "climb_rate": 2, "rot_per_beat": 15, "ring_countdown_from": 4},
   "layers": {"back": ["tiles", "nebula", "stars"], "front": ["dust", "bokeh"]},
   "camera": {"zoom": [1.0, 1.25], "rot": [0, -8], "ease": "inCubic"},  # rot 120→-8: the helix itself spins; a 120° frame roll laid the vertical staircase sideways
   "transition_in": {"type": "spin", "beats": 1.0, "over": True},
   "caption": {"text": "SONSUZA DEK\nYÜKSELİYOR\nGİBİ...", "at": [0.5, 4]},
   "events": [{"at": 2, "kind": "punch"}, {"at": 4, "kind": "rehook", "label": "Shepard yanılsaması, sözsüz gerilim"}, {"at": 6, "kind": "pulse"}]},
  {"id": "S8", "role": "drop", "scene": "mandel_zoom", "beats": 8,
   "params": {"center": [-0.743643887037151, 0.131825904205330], "zoom_start": 1.0, "zoom_per_beat": 1.6, "max_iter": 96,
              "band_on_beat": True, "note_emitters": 4},
   "layers": {"back": ["nebula", "stars", "rays"], "front": ["debris", "dust"]},
   "camera": {"zoom": [1.0, 1.0], "orbit": 4},
   "transition_in": {"type": "flash", "beats": 0.5},
   "caption": {"text": "4 HIZ\n*1* MELODİ", "at": [4, 7.5]},
   "events": [{"at": 2, "kind": "punch"}, {"at": 4, "kind": "rehook", "label": "4 hız / 1 melodi"}, {"at": 6, "kind": "punch"}]},
  {"id": "S9", "role": "reveal", "scene": "object", "beats": 8,
   "params": {"kind": "vinyl", "groove": "spiral_notes", "rpm_beats": 4, "brand": "@hayret.piksel", "brand_at": 0.5,
              "label_text": "SONSUZ\nPLAK", "reveal": 1.5},
   "layers": {"back": ["tiles", "rays", "stars"], "front": ["bokeh", "dust"]},
   "camera": {"zoom": [1.6, 1.0], "ease": "outCubic"},
   "transition_in": {"type": "iris", "beats": 1.0},
   "captions": [{"text": "CEVAP:\nBİR ANLAMDA\n*EVET*", "at": [0.5, 4]},
                {"text": "SERİ SONSUZ\nAMA KULAK\n*SONLU*", "at": [4.5, 7.5]}],
   "events": [{"at": 0, "kind": "reveal", "label": "plak + okunur etiket + ses logosu"}, {"at": 2, "kind": "pulse"},
              {"at": 4, "kind": "punch"}, {"at": 6, "kind": "pulse"}]},
  {"id": "S10", "role": "loop", "scene": "fractal_staff", "beats": 6, "layer_sync": "first",
   "params": {"mode": "nest", "series": "norgard", "rate": 4, "depth": 2, "converge_to_frame0": True, "from_groove": True, "keys": True},
   "layers": {"back": ["horizon", "tiles", {"kind": "nebula", "ramps": ["dim", "energy", "body"]}, "stars"], "front": [{"kind": "bokeh", "ramps": ["pale", "energy"]}, "dust"]},
   "camera": {"zoom": [0.6, 1.0], "ease": "inOutCubic"},
   "transition_in": {"type": "portal", "beats": 1.25},
   "events": [{"at": 2, "kind": "punch"}, {"at": 4, "kind": "pulse"}]}
 ]
}
json.dump(spec, open("spec.json", "w"), ensure_ascii=False, indent=2)

# proxy: same timeline with existing scenes + existing object kind, so validate/sheet can run today
MAP = {"fractal_staff": ("hero", {"branches": 5, "trace": True}), "koch": ("silhouette", {"shape": "star", "assemble": 3}),
       "noise_scope": ("streaks", {}), "series_tree": ("junction", {}), "shepard_stairs": ("chain", {}),
       "mandel_zoom": ("network", {})}
px = copy.deepcopy(spec)
for g in px["segments"]:
    if g["scene"] in MAP:
        g["_target_scene"] = g["scene"]; g["scene"], g["params"] = MAP[g["scene"]][0], dict(MAP[g["scene"]][1])
    elif g["scene"] == "object":
        g["_target_params"] = g["params"]
        g["params"] = {"kind": "jar", "inner": "star", "brand": "@hayret.piksel", "brand_at": 0.5, "reveal": 1.5}
json.dump(px, open("spec_proxy.json", "w"), ensure_ascii=False, indent=2)
print("ok", sum(g["beats"] for g in spec["segments"]), "beats")
