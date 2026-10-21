"""Structure archetypes = optional STARTING POINTS (edit/structure + a matching music design). A spec can ignore
them completely. Each returns a full spec skeleton with {{slots}} for the topic-specific copy.
  python -m bitloop init <dir> --archetype countdown_top_n"""
import copy, json, os

HERE = os.path.dirname(__file__)


def seg(id, role, scene, beats=None, bars=None, tr="cut", cap=None, at=None, params=None, camera=None, events=None, **kw):
    g = {"id": id, "role": role, "scene": scene, "transition_in": tr}
    if bars is not None: g["bars"] = bars
    else: g["beats"] = beats
    if cap: g["caption"] = {"text": cap, "at": at or [0.5, (beats or 4) - .5]}
    if params: g["params"] = params
    if camera: g["camera"] = camera
    if events: g["events"] = events
    g.update(kw); return g


# calm pacing (Oct 2026 feedback): narration sentences instead of 2-word captions, gentler cameras, ≤ 1 punch per
# segment, fast transitions only where the story turns (reveal / number / drop), everything else dissolve/match/slide…
CALM_TR = {"whip": "slide", "glitch": "tiles", "mosaic": "dissolve", "spin": "iris", "crash": "match", "portal": "match",
           "flash": "iris", "split": "split"}
TURN_ROLES = {"reveal", "number", "drop", "hit", "payoff"}


def _slot_text(cap, hook=False):
    hint = cap.replace("{{", "").replace("}}", "").replace("\n", " ").replace("*", "")
    if hook: return "{{kanca: 1 kısa soru/iddia cümlesi, ≤3 satır × ~15 harf, ≤3 s'de okunur — " + hint + "}}"
    return "{{anlatım: tam cümle, ≤5 satır × ~24 harf, anahtar kelime *türkuaz* — " + hint + "}}"


def calm(segments):
    prev = None
    for g in segments:
        cap = g.pop("caption", None)
        if cap:
            hook = g["role"] == "hook"
            g["narration"] = [{"text": _slot_text(cap["text"], hook) if "{{" in cap["text"] else cap["text"], "at": cap["at"][0],
                               "place": "top" if hook else "auto", "size": "head" if hook else "body",
                               "reveal": "word" if hook else "type", "rate": "8th" if hook else "auto"}]
        ev = g.get("events") or []
        punches = [e for e in ev if e.get("kind") == "punch"]
        if punches:
            keep = punches[:1] if g["role"] in TURN_ROLES | {"hook"} else []
            g["events"] = [e for e in ev if e.get("kind") != "punch"] + keep
            if not g["events"]: g.pop("events")
        t = g.get("transition_in", "cut"); ty = t if isinstance(t, str) else t.get("type")
        if ty in CALM_TR and g["role"] not in TURN_ROLES:
            new = CALM_TR[ty]
            if new == prev: new = next(x for x in ("dissolve", "slide", "iris", "tiles", "push", "match") if x != prev)
            g["transition_in"] = new if isinstance(t, str) else {**t, "type": new}
        t = g.get("transition_in", "cut"); prev = t if isinstance(t, str) else t.get("type")
        c = g.get("camera")
        if c and c.get("zoom"):                     # halve the zoom travel (log space), keep its direction
            z0, z1 = c["zoom"]; m = (z0 * z1) ** .5
            c["zoom"] = [round(m * (z0 / m) ** .5, 3), round(m * (z1 / m) ** .5, 3)]
    return segments


def base(title, music, segments, notes, loop_tr="dissolve"):
    segments = calm(segments)
    loop_tr = CALM_TR.get(loop_tr, loop_tr) if loop_tr in ("glitch", "flash", "mosaic") else loop_tr
    return {"version": 2, "preset": "hayret", "pacing": "calm", "_archetype": notes,
            "meta": {"title": title, "description": "{{2 cümle: merak + sayı}}", "hashtags": ["{{#konu}}", "#bilim", "#pixelart", "#hayretpiksel"], "lang": "tr"},
            "format": {"width": 1080, "height": 1920, "fps": 30, "grid": 6},
            "music": music, "loop": True, "loop_beats": 2, "loop_transition": {"type": loop_tr, "beats": 2},
            "segments": segments}


def _punch(*beats): return [{"at": b, "kind": "punch"} for b in beats]


ARCHETYPES = {}


def archetype(fn):
    ARCHETYPES[fn.__name__] = fn; return fn


@archetype
def scale_journey():
    """The reference (Bit Wonder) structure: one protagonist, macro→micro steps, build, hit, big number, metaphor reveal."""
    tpl = json.load(open(os.path.join(HERE, "templates", "reference_scale_journey.json"), encoding="utf-8"))
    segs = tpl["segments"]
    trs = ["cut", "crash", "whip", "dissolve", "match", "portal", "crash", "silhouette", "iris", "dissolve"]
    for g, t in zip(segs, trs): g["transition_in"] = t if t != "silhouette" else {"type": "silhouette", "shape": "{{shape}}"}
    for g in segs:
        if g["role"] == "step" and g["id"] == "S5": g["role"] = "twist"
        nb = g.get("beats", 8)
        if nb >= 9: g["events"] = _punch(*[x for x in (4, 8, 12, 16) if x < nb - 1])
        g.pop("params", None) if g["scene"] not in ("object", "silhouette", "hero") else None
    music = {"style": "hicaz_maqsum", "bpm": 128,
             "sections": [{"name": "intro", "beats": 7, "energy": 1}, {"name": "verse", "beats": 32.5, "energy": 2},
                          {"name": "build", "beats": 8, "energy": 1.5, "riser": True}, {"name": "drop", "beats": 12.5, "energy": 3, "drop": True},
                          {"name": "number", "beats": 9, "energy": 2.5, "fill": True}, {"name": "reveal", "beats": 18, "energy": 2},
                          {"name": "outro", "beats": 7, "energy": 1}]}
    return base("{{BAŞLIK ≤6 kelime + sayı 🎧}}", music, segs, scale_journey.__doc__)


@archetype
def countdown_top_n():
    """Top-N countdown (5→1). Each item = 2 bars with a different transition; riser + stop before #1; #1 is the payoff."""
    S = [seg("S1", "hook", "hero", beats=4, cap="{{EN ŞAŞIRTICI\nN ŞEY?}}", at=[0, 3.5], camera={"zoom": [1.0, 1.25]}, events=_punch(2))]
    trs = ["mosaic", "whip", "tiles", "glitch"]
    scenes = ["lattice", "streaks", "pod", "chain"]
    for k, n in enumerate([5, 4, 3, 2]):
        S.append(seg(f"S{k + 2}", "rehook" if k else "step", scenes[k], bars=2, tr=trs[k], cap=f"*{n}.*\n{{{{MADDE {n}}}}}", at=[0, 4.5],
                     events=_punch(4), camera={"zoom": [1.1, 1.0]}))
    S[3]["role"] = "twist"
    S.append(seg("S6", "build", "junction", beats=4, tr="flash", cap="{{VE 1 NUMARA…}}", at=[0, 3.5]))
    S.append(seg("S7", "reveal", "object", beats=12, tr="iris", cap="*1.*\n{{1 NUMARA}}", at=[1, 7],
                 params={"kind": "{{jar|can|battery|phone}}", "inner": "{{shape}}", "brand": "auto", "brand_at": 2}, events=_punch(4, 8)))
    S.append(seg("S8", "loop", "hero", beats=4, tr="dissolve"))
    music = {"style": "pentatonic_bounce", "sections": [
        {"name": "hook", "bars": 1, "energy": 1.5}, {"name": "list", "bars": 8, "energy": 2, "fill": True},
        {"name": "build", "bars": 1, "energy": 1, "riser": True, "stop": .5}, {"name": "one", "bars": 3, "energy": 3, "drop": True},
        {"name": "out", "bars": 1, "energy": 1.5}]}
    return base("{{N ŞAŞIRTICI …}} 🎧", music, S, countdown_top_n.__doc__, "mosaic")


@archetype
def before_after_reveal():
    """Before/after: minor, half-time 'before' → split screen → key change to major + drop on the 'after'."""
    S = [seg("S1", "hook", "silhouette", beats=4, cap="{{ÖNCE BÖYLE\nGÖRÜNÜYORDU?}}", at=[0, 3.5], params={"shape": "{{shape}}"}, events=_punch(2)),
         seg("S2", "step", "pod", beats=8, tr="push", cap="{{ESKİDEN…?}}", at=[.5, 4], events=_punch(4)),
         seg("S3", "rehook", "chain", beats=8, tr="glitch", cap="{{AMA SONRA\n*SAYI*}}", at=[0, 5], events=_punch(4)),
         seg("S4", "contrast", "network", beats=8, tr={"type": "split", "beats": 4}, cap="{{ÖNCE / SONRA}}", at=[4.5, 7.5]),
         seg("S5", "twist", "streaks", beats=8, tr="whip", cap="{{FARK: *X KAT*}}", at=[.5, 6], events=_punch(4)),
         seg("S6", "build", "junction", beats=4, tr="crash", events=[{"at": 0, "kind": "rehook", "label": "{{peki şimdi?}}"}]),
         seg("S7", "reveal", "object", beats=12, tr="flash", cap="{{ŞİMDİ}}", at=[1.5, 6],
             params={"kind": "{{jar|can|battery|phone}}", "inner": "{{shape}}", "brand": "auto", "brand_at": 1.5}, events=_punch(4, 8)),
         seg("S8", "loop", "silhouette", beats=4, tr="dissolve", params={"shape": "{{shape}}"})]
    music = {"bpm": 84, "meter": "4/4", "key": "A", "scale": "minor", "flavour": "gameboy", "drums": "half_time",
             "progression": ["i", "VI", "III", "VII"], "sections": [
                 {"name": "before", "bars": 5, "energy": 1.5}, {"name": "split", "bars": 2, "energy": 2},
                 {"name": "turn", "bars": 2, "energy": 2.5, "fill": True}, {"name": "build", "bars": 1, "energy": 1, "riser": True},
                 {"name": "after", "bars": 3, "energy": 3, "drop": True, "scale": "major", "progression": ["I", "V", "vi", "IV"], "drums": "four_on_floor"},
                 {"name": "out", "bars": 1, "energy": 1.5}]}
    return base("{{ÖNCE vs SONRA …}} 🎧", music, S, before_after_reveal.__doc__)


@archetype
def process_timeline():
    """Process / how-it-works: numbered stages chained by match cuts and pushes over an aksak 7/8 groove."""
    S = [seg("S1", "hook", "hero", bars=2, cap="{{BU NASIL\nOLUYOR?}}", at=[0, 6], camera={"zoom": [1, 1.3]}, events=_punch(3.5))]
    sc = ["lattice", "chain", "pod", "streaks", "network"]; trs = ["match", "push", "match", {"type": "slide", "dir": "up"}, "tiles"]
    for k in range(5):
        S.append(seg(f"S{k + 2}", "step" if k not in (2,) else "twist", sc[k], bars=2, tr=trs[k], cap=f"*{k + 1}*\n{{{{AŞAMA {k + 1}}}}}", at=[0, 4],
                     events=_punch(3.5)))
    S.append(seg("S7", "payoff", "object", bars=4, tr="portal", cap="{{SONUÇ:\n*SAYI*}}", at=[1, 9],
                 params={"kind": "{{jar|can|battery|phone}}", "inner": "{{shape}}", "brand": "auto", "brand_at": 2}, events=_punch(7, 10.5)))
    S.append(seg("S8", "loop", "hero", bars=1, tr="dissolve"))
    music = {"style": "aksak_phrygian", "sections": [
        {"name": "hook", "bars": 2, "energy": 1.5}, {"name": "stages", "bars": 6, "energy": 2},
        {"name": "stages2", "bars": 4, "energy": 2.5, "fill": True}, {"name": "payoff", "bars": 4, "energy": 3, "drop": True},
        {"name": "out", "bars": 1, "energy": 1}]}
    return base("{{X NASIL ÇALIŞIR?}} 🎧", music, S, process_timeline.__doc__)


@archetype
def myth_vs_fact():
    """Myth vs fact: state the myth (glitchy, unstable), CRT power-off, stop, then the fact lands on a drop."""
    S = [seg("S1", "hook", "hero", beats=6, cap="{{HERKES BUNU\nDOĞRU SANIYOR!}}", at=[0, 5], events=_punch(3)),
         seg("S2", "promise", "network", beats=8, tr="glitch", cap="{{MİT: …}}", at=[.5, 6], events=_punch(4)),
         seg("S3", "step", "chain", beats=8, tr="glitch", cap="{{ÇÜNKÜ…?}}", at=[.5, 6], events=_punch(4)),
         seg("S4", "hold", "void", beats=2, tr="crt", layers={"back": ["horizon", "nebula", "stars"], "front": ["dust"]}),
         seg("S5", "twist", "streaks", beats=8, tr="flash", cap="{{GERÇEK:\n*SAYI*}}", at=[0, 6], events=_punch(4)),
         seg("S6", "rehook", "silhouette", beats=8, tr="silhouette", cap="{{YANİ…}}", at=[1, 6], params={"shape": "{{shape}}"}),
         seg("S7", "reveal", "object", beats=12, tr="iris", cap="{{ASIL\nHAYRET}}", at=[1.5, 6],
             params={"kind": "{{jar|can|battery|phone}}", "inner": "{{shape}}", "brand": "auto", "brand_at": 1.5}, events=_punch(4, 8)),
         seg("S8", "loop", "hero", beats=4, tr="dissolve")]
    music = {"style": "trap_harmonic", "bpm": 130, "sections": [
        {"name": "myth", "beats": 22, "energy": 2}, {"name": "stop", "beats": 2, "energy": 0, "stop": 2},
        {"name": "fact", "beats": 16, "energy": 3, "drop": True, "scale": "major", "progression": ["I", "V", "vi", "IV"]},
        {"name": "reveal", "beats": 12, "energy": 2.5}, {"name": "out", "beats": 4, "energy": 1.5}]}
    return base("{{MİT: … — GERÇEK: …}}", music, S, myth_vs_fact.__doc__, "glitch")


@archetype
def cosmic_zoom_out():
    """Zoom out to cosmic scale: each portal jumps a power of ten; music accelerates (bpm ramp) and opens into lydian."""
    S = [seg("S1", "hook", "pod", beats=4, cap="{{BU NOKTA\nNE KADAR\nKÜÇÜK?}}", at=[0, 3.5], camera={"zoom": [2.2, 1.0]})]
    sc = ["lattice", "hero", "network", "streaks", "silhouette"]
    for k in range(5):
        S.append(seg(f"S{k + 2}", "rehook" if k % 2 else "step", sc[k], beats=6, tr="portal" if k % 2 == 0 else "crash", cap=f"{{{{×10^{k + 1}}}}}", at=[.5, 5],
                     camera={"zoom": [1.8, .8]}, params={"shape": "{{shape}}"} if sc[k] == "silhouette" else None))
    S[4]["role"] = "twist"
    S.append(seg("S7", "reveal", "object", beats=12, tr="iris", cap="{{VE BİZ\n*SAYI*}}", at=[1.5, 7],
                 params={"kind": "globe", "inner": "{{shape}}", "brand": "auto", "brand_at": 2},
                 props=[{"kind": "billboard", "x": 0, "y": 108, "s": 1.0, "layer": "front", "par": 1.0}], events=_punch(4, 8)))
    S.append(seg("S8", "loop", "pod", beats=4, tr="dissolve"))
    music = {"style": "whole_tone_space", "voices": {"lead": {}, "arp": {"min_energy": .5}, "bass": {"pattern": "sustain"}, "pad": {"min_energy": 0}},
             "drums": "half_time", "sections": [
                 {"name": "small", "beats": 16, "energy": 1, "bpm": 84, "bpm_to": 96},
                 {"name": "growing", "beats": 18, "energy": 2, "bpm_to": 112},
                 {"name": "cosmos", "beats": 18, "energy": 3, "drop": True, "scale": "lydian", "progression": ["I", "II", "vi", "V"], "drums": "four_on_floor"},
                 {"name": "out", "beats": 2, "energy": 1, "bpm_to": 84}]}
    return base("{{EVRENDE … 🌌}}", music, S, cosmic_zoom_out.__doc__)


@archetype
def impossible_number():
    """Build-up to an impossible number: numbers escalate every 4–6 s, accelerando + risers, the number lands on the drop."""
    S = [seg("S1", "hook", "hero", beats=4, cap="{{TAHMİN ET:\n*KAÇ?*}}", at=[0, 3.5], events=_punch(2))]
    nums = ["{{*10*}}", "{{*1.000*}}", "{{*1 MİLYON*}}", "{{*1 MİLYAR*}}"]; sc = ["pod", "lattice", "streaks", "network"]
    trs = ["mosaic", "push", "whip", "glitch"]
    for k in range(4):
        S.append(seg(f"S{k + 2}", "rehook", sc[k], beats=8, tr=trs[k], cap=nums[k], at=[0, 4.5], events=_punch(4), camera={"zoom": [1, 1.25]}))
    S[3]["role"] = "twist"
    S.append(seg("S6", "build", "junction", beats=4, tr="crash", cap="{{DAHA DA…}}", at=[0, 3]))
    S.append(seg("S7", "number", "silhouette", beats=8, tr="flash", cap="{{*İMKÂNSIZ\nSAYI*}}", at=[0, 7], params={"shape": "{{shape}}"}, events=_punch(4)))
    S.append(seg("S8", "payoff", "object", beats=10, tr="iris", cap="{{YANİ\nHER GÜN…}}", at=[1.5, 7],
                 params={"kind": "{{jar|can|battery|phone}}", "inner": "{{shape}}", "brand": "auto", "brand_at": 1.5}, events=_punch(5)))
    S.append(seg("S9", "loop", "hero", beats=4, tr="dissolve"))
    music = {"style": "synthwave_major", "sections": [
        {"name": "guess", "beats": 12, "energy": 1.5, "bpm": 100, "bpm_to": 108}, {"name": "climb", "beats": 24, "energy": 2.5, "bpm_to": 124, "fill": True},
        {"name": "build", "beats": 4, "energy": 1, "riser": True, "stop": .5},
        {"name": "number", "beats": 8, "energy": 3, "drop": True, "transpose": 2},
        {"name": "payoff", "beats": 10, "energy": 2, "transpose": 2, "bpm_to": 116}, {"name": "out", "beats": 4, "energy": 1.5, "bpm_to": 100}]}
    return base("{{… KAÇ TANE? 🤯}}", music, S, impossible_number.__doc__, "flash")


@archetype
def story_vignette():
    """Micro story: a character (hero/image), a problem, a surprising turn, the science answer, a warm payoff."""
    S = [seg("S1", "hook", "hero", beats=6, cap="{{BİR GÜN\n… OLURSA?}}", at=[0, 5], events=_punch(3)),
         seg("S2", "promise", "image", beats=9, tr="iris", cap="{{SORUN: …?}}", at=[1, 6], params={"image": "{{karakter.png}}"}, events=_punch(4.5)),
         seg("S3", "rehook", "chain", beats=9, tr="slide", cap="{{İLK DENEME?}}", at=[1, 6], events=_punch(4.5)),
         seg("S4", "twist", "network", beats=9, tr="glitch", cap="{{AMA…\n*SAYI*}}", at=[0, 6], events=_punch(4.5)),
         seg("S5", "build", "junction", beats=6, tr="tiles", events=[{"at": 2, "kind": "rehook", "label": "{{yeni soru}}"}]),
         seg("S6", "reveal", "object", beats=12, tr="flash", cap="{{ÇÖZÜM}}", at=[1.5, 7],
             params={"kind": "{{jar|can|battery|phone}}", "inner": "{{shape}}", "brand": "auto", "brand_at": 1.5}, events=_punch(4.5, 9)),
         seg("S7", "loop", "hero", beats=3, tr="dissolve")]
    music = {"style": "lydian_waltz", "sections": [
        {"name": "once", "bars": 5, "energy": 1.5}, {"name": "try", "bars": 3, "energy": 2},
        {"name": "turn", "bars": 3, "energy": 2.5, "scale": "harmonic_minor", "progression": ["i", "iv", "V", "i"]},
        {"name": "build", "bars": 2, "energy": 1, "riser": True, "stop": .5}, {"name": "answer", "bars": 4, "energy": 3, "drop": True, "scale": "lydian", "progression": ["I", "II", "V", "I"]},
        {"name": "out", "bars": 1, "energy": 1.5, "bpm_to": 80}]}
    return base("{{… OLSAYDI? 🎧}}", music, S, story_vignette.__doc__)


def make(name):
    if name not in ARCHETYPES: raise ValueError(f"unknown archetype '{name}' — {', '.join(ARCHETYPES)}")
    return copy.deepcopy(ARCHETYPES[name]())
