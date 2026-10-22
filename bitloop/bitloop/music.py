"""Composable chiptune engine. One spec → a beat-locked, deterministic (seeded) soundtrack.

music = {
  style?   starting point from STYLES (any key below overrides it)
  bpm, meter ("7/8"), grouping ([2,2,3]), key ("E"), scale (theory.SCALES), tuning ("12tet"|"approx"),
  flavour ("2a03"|"gameboy"|"sid"|"fm"), progression (["i","bII","V7"] | ["Em","C"] | [["E3","G3","B3"]]),
  chord_bars (harmonic rhythm), swing, seed,
  voices   {name: {role: lead|counter|arp|bass|pad, type, duty, pwm, sweep, vibrato, arp, glide, octave, vol, pan,
                   echo, env{a,d,s,r}, pattern, rate, min_energy, table, ratio, index, filter,
                   series{name, rate, div, sign|invert, phase: global|section, offset, logo_duck}}}
           series: the voice plays an integer series (theory.SERIES, e.g. Nørgård's infinity series) as ABSOLUTE scale
           degrees from the section key, one note every 1/(rate/div) beats on the GLOBAL beat grid (index =
           floor(beat*rate/div)), so voices at different speeds stay self-similar across sections. Overrides
           pattern/motif for any role.
  drums    pattern name | custom grid {"K":"x...","S":"....x..."} | "auto" | "none"
  motif    {"notes":[0,2,4,null], "rhythm":[.5]} | {"contour":"arch","range":7,"density":.6,"seed":3}
  sections [{name, bars|beats, energy, bpm, bpm_to, meter, grouping, key, scale, transpose, progression, chord_bars,
             voices | voices_in | voices_out, gain {voice: k} (per-section series-voice trim), level_db (section music level), drums, fill, riser, riser_kind (noise|shepard), shepard_hops, stop, drop,
             swing}]   (omit → one per video segment)
  logo     true | {"at": ["reveal","loop"] | [beats], "voice": "lead"}
  sfx      true | false | {"hit": "boom", "tick": null, ...}   (event-kind remap)
  breath   beats of silence before every drop (default 0.5) · lufs (-14) · limit_ceiling (.6 linear start ceiling of the
           safety limiter; the AAC true-peak check still lowers it to ≤ −1.2 dBTP) · source synth|file · file · offset }
"""
import copy, math, os, subprocess, tempfile, wave
import numpy as np
from .timing import Meter, TempoMap, tempo_map
from .theory import Scale, chord as mkchord, motif as mkmotif, NOTE, series_value
from .voices import SR, note as vnote, voice_cfg, hz
from . import drums as D
from . import sfx as SFX

STYLES = {
    "reference":        {"bpm": 117.45, "meter": "4/4", "key": "D", "scale": "minor", "flavour": "2a03",
                         "progression": ["i", "VI", "III", "VII"], "drums": "four_on_floor", "logo": False},
    "hicaz_maqsum":     {"bpm": 112, "meter": "4/4", "key": "D", "scale": "hicaz", "flavour": "2a03",
                         "progression": ["I", "II", "IV", "I"], "drums": "maqsum", "voices": {"arp": {"pattern": "updown"}}},
    "aksak_phrygian":   {"bpm": 140, "meter": "7/8", "key": "E", "scale": "phrygian", "flavour": "sid",
                         "progression": ["I", "II", "I", "VII"], "drums": "aksak_7_8",
                         "voices": {"arp": {"pattern": "groups", "rate": 2}, "bass": {"pattern": "groups"}}},
    "lydian_waltz":     {"bpm": 90, "meter": "3/4", "key": "F", "scale": "lydian", "flavour": "fm",
                         "progression": ["I", "II", "V", "I"], "drums": "waltz",
                         "voices": {"arp": {"pattern": "oompah"}, "bass": {"pattern": "waltz"}, "lead": {"vibrato": .12},
                                    "counter": {"role": "arp", "pattern": "up", "rate": 3, "octave": 6, "vol": .03, "min_energy": 2}}},
    "halftime_minor":   {"bpm": 75, "meter": "4/4", "key": "A", "scale": "minor", "flavour": "gameboy",
                         "progression": ["I", "VI", "III", "VII"], "drums": "half_time", "chord_bars": 1,
                         "voices": {"arp": {"pattern": "broken", "rate": 4}, "bass": {"pattern": "sustain"}, "pad": {"min_energy": .5}}},
    "synthwave_major":  {"bpm": 100, "meter": "4/4", "key": "C", "scale": "major", "flavour": "sid",
                         "progression": ["vi", "IV", "I", "V"], "drums": "four_on_floor", "voices": {"bass": {"pattern": "octave"}}},
    "trap_harmonic":    {"bpm": 140, "meter": "4/4", "key": "C#", "scale": "harmonic_minor", "flavour": "fm",
                         "progression": ["i", "VI", "iv", "V"], "drums": "trap", "voices": {"bass": {"pattern": "sustain", "glide": .06}}},
    "pentatonic_bounce": {"bpm": 128, "meter": "4/4", "key": "G", "scale": "pentatonic_major", "flavour": "gameboy",
                         "progression": ["I", "IV", "I", "V"], "drums": "breakbeat"},
    "whole_tone_space": {"bpm": 84, "meter": "4/4", "key": "C", "scale": "whole_tone", "flavour": "fm",
                         "progression": ["I", "II", "I", "VI"], "drums": "none", "voices": {"pad": {"min_energy": 0}}},
    "rast_aksak":       {"bpm": 132, "meter": "9/8", "key": "G", "scale": "rast", "tuning": "approx", "flavour": "2a03",
                         "progression": ["I", "IV", "V", "I"], "drums": "aksak_9_8"},
    "nihavend_six_eight": {"bpm": 96, "meter": "6/8", "key": "C", "scale": "nihavend", "flavour": "fm",
                         "progression": ["i", "iv", "V", "i"], "drums": "six_eight"},
    "blues_shuffle":    {"bpm": 104, "meter": "4/4", "key": "E", "scale": "blues", "flavour": "2a03",
                         "progression": ["I7", "IV7", "I7", "V7"], "drums": "shuffle", "swing": .8},
}
ROLE_DEFAULTS = {
    "lead":    {"octave": 5, "vol": .075, "pan": .2, "echo": .75, "min_energy": 2.0, "env": {"d": .2, "s": .4}},
    "counter": {"octave": 4, "vol": .045, "pan": -.25, "min_energy": 2.5, "env": {"d": .2, "s": .3}},
    "arp":     {"octave": 5, "vol": .06, "pan": -.35, "rate": 4, "pattern": "up", "min_energy": 1.0, "env": {"d": .05, "s": 0}},
    "bass":    {"octave": 2, "vol": .30, "pan": 0, "rate": 2, "pattern": "chip", "min_energy": .5, "env": {"d": .25, "s": .5}},
    "pad":     {"octave": 4, "vol": .035, "pan": 0, "min_energy": 1.5, "env": {"a": .08, "d": .6, "s": .55, "r": .2}},
}
DEFAULT_VOICES = {"lead": {}, "arp": {}, "bass": {}, "pad": {}}
ARP = {"up": [0, 1, 2, 3], "down": [3, 2, 1, 0], "updown": [0, 1, 2, 3, 2, 1], "broken": [0, 2, 1, 3], "alberti": [0, 2, 1, 2],
       "pedal": [0, 3, 1, 3, 2, 3]}
BASS = {"chip": [0, 0, "5", 0, 12, 0, "5", "3"], "root8": [0], "octave": [0, 12], "walk": ["1", "3", "5", "6"],
        "pump": [0, None, 0, 0]}
LOGO_RHYTHM = [(0.0, .5), (.5, .5), (1.0, .5), (1.5, 1.75)]       # short-short-short-LONG (beats); long lands on the target


# ------------------------------------------------------------------ spec resolution
def resolve(spec, seg_beats_fn):
    """Fill music defaults, resolve sections and the tempo map. seg_beats_fn(meter_at) -> list of segment beats.
    Writes spec['_sections'] and spec['_tempo'] (JSON-safe)."""
    m = spec.setdefault("music", {})
    st = STYLES.get(m.get("style")) if m.get("style") else None
    if m.get("style") and st is None: raise ValueError(f"unknown music style '{m['style']}' — {', '.join(STYLES)}")
    if st:
        for k, v in copy.deepcopy(st).items():
            if k == "voices" and "voices" in m: continue
            m.setdefault(k, v)
        if "voices" not in m and "voices" in st: m["voices"] = {**DEFAULT_VOICES, **copy.deepcopy(st["voices"])}
    if "mode" in m and "scale" not in m: m["scale"] = m.pop("mode")               # v1 compatibility
    if "kit" in m and "drums" not in m: m["drums"] = {"four": "four_on_floor", "maqsum": "maqsum"}.get(m.pop("kit"), "auto")
    if isinstance(m.get("arp"), str):
        m.setdefault("voices", copy.deepcopy(DEFAULT_VOICES)).setdefault("arp", {})["pattern"] = m.pop("arp")
    for k, v in {"bpm": 112.0, "meter": "4/4", "key": "D", "scale": "minor", "tuning": "12tet", "flavour": "2a03",
                 "progression": ["i", "VI", "III", "VII"], "chord_bars": 1, "drums": "auto", "swing": 0.0, "seed": 7,
                 "breath": .5, "logo": True, "sfx": True, "lufs": -14.0, "source": "synth", "file": None, "offset": 0.0}.items():
        m.setdefault(k, v)
    m.setdefault("voices", copy.deepcopy(DEFAULT_VOICES))
    base = {"bpm": float(m["bpm"]), "meter": m["meter"], "grouping": m.get("grouping"), "key": m["key"], "scale": m["scale"],
            "tuning": m["tuning"], "progression": m["progression"], "chord_bars": m["chord_bars"], "drums": m["drums"],
            "swing": m["swing"], "transpose": 0}
    raw = m.get("sections")
    secs, b = [], 0.0
    if raw:
        cur = dict(base)
        for i, r in enumerate(raw):
            cur = {**cur, **{k: v for k, v in r.items() if k in base}}
            me = Meter(cur["meter"], r.get("grouping") if "meter" in r else cur.get("grouping"))
            beats = float(r["beats"]) if "beats" in r else float(r.get("bars", 2)) * me.bar_beats
            s = {**cur, "name": r.get("name", f"sec{i + 1}"), "b0": b, "b1": b + beats, "energy": float(r.get("energy", 1.5)),
                 "bpm": float(cur["bpm"]), "bpm_to": float(r.get("bpm_to", cur["bpm"])), "grouping": me.grouping,
                 "voices": r.get("voices"), "voices_in": r.get("voices_in", []), "voices_out": r.get("voices_out", []),
                 "fill": bool(r.get("fill")), "riser": bool(r.get("riser")), "stop": float(r.get("stop", 0)),
                 "riser_kind": r.get("riser_kind", "noise"), "shepard_hops": float(r.get("shepard_hops", 2)),
                 "drop": bool(r.get("drop")), "explicit_drums": "drums" in r, "gain": dict(r.get("gain") or {}),
                 "level_db": float(r.get("level_db", 0.0))}
            secs.append(s); b += beats
            cur["bpm"] = s["bpm_to"]
    meter_at = lambda beat: _meter_at(secs, beat, base)
    seg_beats = seg_beats_fn(meter_at)
    total = float(sum(seg_beats))
    if not raw:   # one section per video segment, behaviour from its role
        sb = 0.0
        for g, nb in zip(spec.get("segments", []), seg_beats):
            role = g.get("role", "free")
            secs.append({**base, "name": g.get("id"), "b0": sb, "b1": sb + nb, "energy": float(g.get("energy", 1.5)),
                         "bpm_to": base["bpm"], "grouping": Meter(base["meter"], base["grouping"]).grouping,
                         "voices": None, "voices_in": [], "voices_out": [], "fill": False,
                         "riser": role == "build", "stop": 1.0 if role == "hold" else 0.0, "riser_kind": "noise", "shepard_hops": 2.0,
                         "drop": role in ("hit", "drop"), "explicit_drums": False})
            sb += nb
    if secs:
        if secs[-1]["b1"] < total: secs[-1]["b1"] = total
        secs = [s for s in secs if s["b0"] < total - 1e-9] or secs[:1]
        secs[-1]["b1"] = total
    pieces = [(s["b0"], s["b1"], s["bpm"], s["bpm_to"]) for s in secs] or [(0, total, base["bpm"], base["bpm"])]
    spec["_sections"] = secs; spec["_tempo"] = [list(p) for p in pieces]
    return seg_beats, total


def _meter_at(secs, beat, base):
    for s in secs:
        if s["b0"] <= beat < s["b1"] - 1e-9: return Meter(s["meter"], s["grouping"])
    if secs: return Meter(secs[-1]["meter"], secs[-1]["grouping"])
    return Meter(base["meter"], base.get("grouping"))


def section_at(spec, beat):
    for s in spec["_sections"]:
        if s["b0"] <= beat < s["b1"]: return s
    return spec["_sections"][-1]


# ------------------------------------------------------------------ mixing
def _section_levels(spec, mix, tm, ramp_s=.04):
    """sections[].level_db: a per-section music level (dynamic arc: quiet reflection, louder drop) applied to the
    synth mix BEFORE SFX; ±ramp_s crossfade around each boundary, so tails and pickups never click. 0 dB = no-op."""
    secs = spec.get("_sections") or []
    if not any(abs(s.get("level_db", 0.0)) > 1e-6 for s in secs): return
    t = np.arange(len(mix.L)) / SR - Mix.PRE
    edges = [tm.time(s["b0"]) for s in secs[1:]]
    lv = [10 ** (s.get("level_db", 0.0) / 20) for s in secs]
    g = np.full(len(t), lv[0])
    for e, a, b in zip(edges, lv, lv[1:]):
        k = np.clip((t - e + ramp_s) / (2 * ramp_s), 0, 1); g = np.where(t >= e - ramp_s, a + (b - a) * k, g)
    mix.L *= g; mix.R *= g


class Mix:
    PRE = 4.0      # seconds of pre-roll so pickups/risers before t=0 survive (and wrap to the end on loops)

    def __init__(self, seconds):
        self.L = np.zeros(int((seconds + self.PRE) * SR) + SR); self.R = np.zeros_like(self.L)

    def add(self, t, sig, vol=1.0, pan=0.0):
        i = int(round((t + self.PRE) * SR))
        if i >= len(self.L) or i + len(sig) <= 0: return
        if i < 0: sig = sig[-i:]; i = 0
        j = min(len(self.L), i + len(sig)); s = sig[:j - i] * vol
        self.L[i:j] += s * (1 - max(0, pan)); self.R[i:j] += s * (1 + min(0, pan))


def logo_targets(spec):
    """Beats where the LONG logo note lands: the reveal downbeat (first reveal/payoff/metaphor segment, or the
    segment carrying the legible tag) and beat 0 of the loop seam (= total). Explicit beats allowed."""
    lg = spec["music"].get("logo")
    if not lg: return []
    at = lg.get("at", ["reveal", "loop"]) if isinstance(lg, dict) else ["reveal", "loop"]
    out = []
    for a in at:
        if isinstance(a, (int, float)): out.append(float(a)); continue
        if a == "reveal":
            for g in spec["segments"]:
                if g.get("role") in ("reveal", "payoff", "metaphor") or (g.get("scene") == "object" and g["params"].get("brand")):
                    out.append(g["start_beat"] + float(g["params"].get("brand_at", 0)) if g.get("scene") == "object" else g["start_beat"]); break
        if a == "loop" and spec.get("loop"):
            if not any(abs(spec["total_beats"] - o) < 6 for o in out): out.append(spec["total_beats"])
        if a == "end" and not spec.get("loop"): out.append(max(1.5, spec["total_beats"] - 2.5))
    return sorted(set(out))


def _math_callable(name):
    """Resolve a spec math_fn string ("hardtekk" / "from_scene:phonk808") to the SAME callable the visual scene uses."""
    from .scenes_mathlab import FORMULA
    key = str(name or "hardtekk")
    if key.startswith("from_scene:"):
        key = key.split(":", 1)[1]
    return FORMULA.get(key, FORMULA["hardtekk"])["f"]


def _voices(spec):
    m = spec["music"]; fl = m["flavour"]; out = {}
    for name, u in m["voices"].items():
        if u is None: continue
        v = voice_cfg(name, u, fl); rd = ROLE_DEFAULTS.get(v["role"], ROLE_DEFAULTS["lead"])
        for k, val in rd.items():
            if k == "env": v["env"] = {**val, **v.get("env", {})}
            else: v.setdefault(k, val)
        v["_name"] = name
        if v.get("type") == "math":
            v["math_fn"] = _math_callable(v.get("math_fn"))
        out[name] = v
    return out


def _active(sec, voices):
    if sec["voices"] is not None: act = set(sec["voices"])
    else: act = {n for n, v in voices.items() if sec["energy"] >= v["min_energy"]}
    act |= set(sec["voices_in"]); act -= set(sec["voices_out"])
    if sec["riser"] and sec["voices"] is None: act -= {n for n, v in voices.items() if v["role"] in ("lead", "counter")}
    return act


def synth(spec, out_wav, music=True):
    from .spec import timeline_events
    m = spec["music"]; tm = tempo_map(spec); T = spec["duration_s"]; total = spec["total_beats"]
    rng = np.random.default_rng(m["seed"]); fl = m["flavour"]
    mix = Mix(T + 6); voices = _voices(spec)
    logos = logo_targets(spec)
    logo_win = logo_windows(spec, logos)
    drops = [s["b0"] for s in spec["_sections"] if s["drop"]]
    breath = float(m.get("breath", .5))
    def silent(b):
        if any(d - breath <= b < d for d in drops if d > 0): return True
        s = section_at(spec, b)
        return s["stop"] > 0 and b >= s["b1"] - s["stop"]
    motifs = {}
    def get_motif(me):
        if me.sig not in motifs: motifs[me.sig] = mkmotif(m.get("motif"), me, np.random.default_rng(m["seed"] + 11), bars=2)
        return motifs[me.sig]
    def T_(b): return tm.time(b)
    def add_note(v, midi, b, d, vol_k=1.0, glide_from=None):
        t0 = T_(b); dur = max(.02, T_(b + d) - t0)
        sig = vnote({**v, "_seed": int(b * 97)}, midi, dur, glide_from, fl)
        mix.add(t0, sig, v["vol"] * vol_k, v["pan"])
        if v.get("echo"):
            mix.add(T_(b + v["echo"]), sig, v["vol"] * vol_k * .38, -v["pan"] * 1.5 if v["pan"] else .4)
    if music and m["source"] == "synth":
        for sec in spec["_sections"]:
            me = Meter(sec["meter"], sec["grouping"])
            sc = Scale(_shift_key(sec["key"], sec.get("transpose", 0)), sec["scale"], sec["tuning"])
            act = _active(sec, voices); prog = sec["progression"]
            cb = max(.5, float(sec["chord_bars"]) * me.bar_beats)
            pat = None if (sec["riser"] and not sec["explicit_drums"]) else D.resolve(sec["drums"], me)
            if pat is not None and sec.get("swing"): pat["swing"] = sec["swing"]
            mot, mlen = get_motif(me)
            nb = int(math.ceil((sec["b1"] - sec["b0"]) / me.bar_beats - 1e-9))
            prev_bass = None
            for bar in range(nb):
                b_bar = sec["b0"] + bar * me.bar_beats
                # ---- drums
                if pat is not None and sec["energy"] > 0:
                    last = bar == nb - 1 and sec["fill"]
                    for off, inst, vel in D.hits_in_bar(pat, me, sec["energy"], fill=last, bar=bar):
                        b = b_bar + off
                        if b >= sec["b1"] or silent(b): continue
                        mix.add(T_(b), D.drum(inst, fl, int(b * 13)), D.VOL[inst] * vel, D.PAN.get(inst, 0))
                # ---- harmony per chord slot inside the bar
                k = 0.0
                while k < me.bar_beats - 1e-9:
                    b_ch = b_bar + k
                    if b_ch >= sec["b1"]: break
                    ci = int(round((b_ch - sec["b0"]) / cb)) % len(prog)
                    ch = mkchord(prog[ci], sc, 3)
                    seg_len = min(cb, me.bar_beats - k, sec["b1"] - b_ch)
                    for name in act:
                        v = voices[name]; role = v["role"]
                        if v.get("series"): continue
                        if role == "pad":
                            if not silent(b_ch):
                                notes = ch[:int(v.get("max_notes", 4))]     # pad.max_notes (default 4); >4 notes: 1/√n per note
                                gk = .8 if len(notes) <= 4 else .8 * 2 / math.sqrt(len(notes))
                                for p in notes: add_note(v, p + 12 * (v["octave"] - 3), b_ch, seg_len * .98, gk)
                        elif role == "arp":
                            rate = v["rate"]; step = 1.0 / rate
                            tones = sorted(ch[:3]) + [min(ch) + 12] if len(ch) <= 4 else sorted(ch) + [min(ch) + 12]
                            while len(tones) < 4: tones.append(tones[-1] + 12)      # 1–2-note chords: octave-stack
                            if v["pattern"] == "oompah":      # chord stabs on every pulse except the downbeat
                                for gi, g in enumerate(me.group_starts):
                                    bb = b_bar + g
                                    if gi == 0 or not (b_ch <= bb < b_ch + seg_len) or silent(bb): continue
                                    for p in sorted(ch[:3]): add_note({**v, "echo": 0}, p + 12 * (v["octave"] - 4), bb, .45, .55)
                                continue
                            if v["pattern"] == "groups":
                                order = None
                            else:
                                order = ARP.get(v["pattern"], ARP["up"])
                            j = 0; bb = b_ch
                            while bb < b_ch + seg_len - 1e-9:
                                if not silent(bb):
                                    if order is None:
                                        gi = sum(1 for g in me.group_starts if g <= (bb - b_bar) + 1e-9) - 1
                                        idx = (j + gi) % 4
                                    elif len(tones) > 4 and v["pattern"] in ("up", "down"):   # clusters: run through all tones
                                        idx = j % len(tones) if v["pattern"] == "up" else -1 - j % len(tones)
                                    elif v["pattern"] == "random":     # seeded, beat-anchored, never the same tone twice in a row
                                        n_ = int(round(bb * rate)); hsh = lambda q: int((math.sin(q * 12.9898 + m['seed'] * .0137 * 78.233) * 43758.5453) % 1 * 997)
                                        idx = hsh(n_) % len(tones); last = v.get("_last_rand")
                                        if last is not None and tones[idx] + 12 * (v["octave"] - 3) == last:   # compare pitches (chords repeat tones)
                                            alt = [k for k in range(len(tones)) if tones[k] + 12 * (v["octave"] - 3) != last]
                                            if alt: idx = alt[hsh(n_ + 7) % len(alt)]
                                        v["_last_rand"] = tones[idx] + 12 * (v["octave"] - 3)
                                    else: idx = order[j % len(order)]
                                    add_note(v, tones[idx] + 12 * (v["octave"] - 3), bb, step * .9, 1.0 if j % rate == 0 else .75)
                                bb += step; j += 1
                        elif role == "bass":
                            root = min(ch); fifth = sorted(ch)[2] if len(ch) > 2 else root + 7
                            third = sorted(ch)[1] if len(ch) > 1 else root + 4         # one-note chords used to crash here
                            base_m = root + 12 * (v["octave"] - 3)
                            pt = v["pattern"]
                            if pt == "sustain":
                                if not silent(b_ch): add_note(v, base_m, b_ch, seg_len * .97, 1.0, prev_bass); prev_bass = base_m
                                continue
                            if pt in ("groups", "waltz"):
                                for gi, g in enumerate(me.group_starts):
                                    bb = b_bar + g
                                    if not (b_ch <= bb < b_ch + seg_len) or silent(bb): continue
                                    if pt == "waltz" and gi > 0: continue
                                    p = base_m if gi == 0 else base_m + (fifth - root) * (gi % 2) + 12 * (gi % 2 == 0)
                                    gl = (me.group_starts + [me.bar_beats])[gi + 1] - g
                                    add_note(v, p, bb, gl * .9)
                                continue
                            seq = v["pattern"] if isinstance(v["pattern"], list) else BASS.get(pt, BASS["chip"])
                            step = 1.0 / v["rate"]; j = 0; bb = b_ch
                            while bb < b_ch + seg_len - 1e-9:
                                o = seq[j % len(seq)]
                                if o is not None and not silent(bb):
                                    if isinstance(o, str):
                                        o = {"1": 0, "3": third - root, "5": fifth - root, "6": (fifth - root) + 2, "7": 10}[o]
                                    add_note(v, base_m + o, bb, step * .92, 1.0, prev_bass); prev_bass = base_m + o
                                bb += step; j += 1
                    k += seg_len
                # ---- melody (lead / counter) from the motif, phrase A A' over 2-bar cycles
                for name in act:
                    v = voices[name]
                    if v["role"] not in ("lead", "counter") or v.get("series"): continue
                    cyc = int(((b_bar - sec["b0"]) // mlen)) if mlen else 0
                    within = (b_bar - sec["b0"]) % mlen if mlen else 0
                    for off, d, deg in mot:
                        if not (within <= off < within + me.bar_beats) or deg is None: continue
                        b = b_bar + (off - within)
                        if b >= sec["b1"] or silent(b) or any(a <= b < z for a, z in logo_win): continue
                        ci = int(round((b - sec["b0"]) / cb - .4999)) % len(prog)
                        cd = _chord_degree(mkchord(prog[ci], sc, 3), sc)
                        dd = deg + (1 if (cyc % 2 and off >= mlen - 1) else 0)
                        if v["role"] == "counter": dd -= 2
                        p = sc.degree(cd + dd, v["octave"] - 1)
                        add_note(v, p, b, min(d, sec["b1"] - b))
            # ---- series voices (global beat grid, not per bar / per section)
            for name in sorted(act):
                v = voices[name]
                if not v.get("series"): continue
                si = spec["_sections"].index(sec); nxt = spec["_sections"][si + 1] if si + 1 < len(spec["_sections"]) else None
                cut = nxt is None or name not in _active(nxt, voices) or nxt["scale"] != sec["scale"] or nxt["key"] != sec["key"]
                for b, dur, midi, vk in series_notes(v, sec, sc, silent_end=lambda b: _silent_from(spec, b, breath, drops),
                                                     logo_win=logo_win, silent=silent, cut_at_end=cut):
                    add_note(v, midi, b, dur, vk)
            if sec["riser"] and sec.get("riser_kind") == "shepard":
                _shepard(spec, mix, tm, sec, rng)
        # ---- sonic logo, transposed into the key/scale/timbre at its target
        for lb in logos:
            _logo(spec, mix, tm, lb, voices, fl)
    _section_levels(spec, mix, tm)
    if m.get("sfx", True):
        remap = m["sfx"] if isinstance(m["sfx"], dict) else {}
        for b, kind, _ in timeline_events(spec):
            base = kind.partition("@")[0]
            kind = remap[base] if base in remap else remap.get(kind, kind)
            if not kind: continue
            sec = section_at(spec, min(max(b, 0), total - 1e-6))
            root = 36 + (NOTE[_shift_key(sec["key"], sec.get("transpose", 0)).upper()])
            SFX.mix(mix, T_(b), kind, root, tm.beat_len(max(b, 0)))
    n = int(T * SR); P = int(Mix.PRE * SR)
    L, R = mix.L[P:P + n].copy(), mix.R[P:P + n].copy()
    if spec.get("loop"):      # seamless: release tails wrap into the start, pre-roll (pickups/risers) into the end
        tl = mix.L[P + n:]; k = min(len(tl), n); L[:k] += tl[:k]; R[:k] += mix.R[P + n:P + n + k]
        k = min(P, n); L[n - k:] += mix.L[P - k:P]; R[n - k:] += mix.R[P - k:P]
    if not spec.get("loop"):
        f = np.clip((T - np.arange(n) / SR) / 1.5, 0, 1); L *= f; R *= f
    st = np.stack([L, R], 1); pk = np.abs(st).max() or 1
    _write(out_wav, st / pk * .89)
    return out_wav


def drum_hits(spec, inst):
    """Beats at which drum `inst` actually sounds (same gating as synth: energy, stops, drop breaths, riser) —
    the picture syncs to these (e.g. the sonar vision fires a ring on every 'B' chirp)."""
    m = spec["music"]
    if m.get("source", "synth") != "synth": return []
    drops = [s["b0"] for s in spec["_sections"] if s["drop"]]; breath = float(m.get("breath", .5))
    def silent(b):
        if any(d - breath <= b < d for d in drops if d > 0): return True
        s = section_at(spec, b)
        return s["stop"] > 0 and b >= s["b1"] - s["stop"]
    out = []
    for sec in spec["_sections"]:
        me = Meter(sec["meter"], sec["grouping"])
        pat = None if (sec["riser"] and not sec["explicit_drums"]) else D.resolve(sec["drums"], me)
        if pat is None or sec["energy"] <= 0: continue
        if sec.get("swing"): pat["swing"] = sec["swing"]
        nb = int(math.ceil((sec["b1"] - sec["b0"]) / me.bar_beats - 1e-9))
        for bar in range(nb):
            b_bar = sec["b0"] + bar * me.bar_beats
            for off, i_, vel in D.hits_in_bar(pat, me, sec["energy"], fill=bar == nb - 1 and sec["fill"], bar=bar):
                b = b_bar + off
                if i_ == inst and b < sec["b1"] and not silent(b): out.append(round(b, 6))
    return sorted(out)


def logo_windows(spec, logos=None):
    """Beat windows owned by the sonic logo (melody voices yield / duck). On loops the seam window wraps to beat 0."""
    logos = logo_targets(spec) if logos is None else logos
    total = spec["total_beats"]; out = []
    for lb in logos:
        a, z = lb - 1.5, lb + 1.75
        out.append((a, z))
        if spec.get("loop"):
            if z > total: out.append((a - total, z - total))
            if a < 0: out.append((a + total, z + total))
    return out


def _silent_from(spec, b, breath, drops):
    """Beat where the next silence (held breath before a drop, section stop) starts after beat b (inf if none)."""
    c = [d - breath for d in drops if d - breath > b + 1e-9]
    c += [s["b1"] - s["stop"] for s in spec["_sections"] if s["stop"] > 0 and s["b1"] - s["stop"] > b + 1e-9]
    return min(c) if c else float("inf")


def series_cfg(v):
    ss = v["series"]; ss = {"name": ss} if isinstance(ss, str) else dict(ss)
    ss.setdefault("name", "norgard")
    ss["_rate"] = float(ss.get("rate", v.get("rate", 4))) / float(ss.get("div", 1) or 1)
    ss["_sign"] = (-1 if ss.get("invert") else 1) * (1 if ss.get("sign", 1) >= 0 else -1)
    return ss


def series_notes(v, sec, sc, silent_end=None, logo_win=(), silent=None, cut_at_end=False):
    """Notes of a series voice inside one section → [(beat, dur_beats, midi, vol_k)].
    Index = floor(beat*rate) on the GLOBAL grid (phase 'section' restarts at the section start), plus `lookahead` k
    (slot n plays value n+k: the voice is k notes in the future); degree = sign*a(i)+offset,
    absolute in the section scale at the voice octave. Duration = gate/rate (default .92), cut at the next silence."""
    ss = series_cfg(v); rate = ss["_rate"]; gate = float(ss.get("gate", .92)); off = int(ss.get("offset", 0))
    duck = float(ss.get("logo_duck", .3)); melodic = v["role"] in ("lead", "counter")
    n = int(math.ceil(sec["b0"] * rate - 1e-9)); n0 = n if ss.get("phase") == "section" else 0
    out = []
    while n / rate < sec["b1"] - 1e-9:
        b = n / rate
        if not (silent and silent(b)):
            d = ss["_sign"] * int(series_value(ss["name"], n - n0 + int(ss.get("lookahead", 0)))) + off
            end = b + gate / rate
            if silent_end: end = min(end, silent_end(b))
            if cut_at_end: end = min(end, sec["b1"])
            vk = duck if (melodic and any(a <= b < z for a, z in logo_win)) else 1.0
            vk *= float(sec.get("gain", {}).get(v.get("_name", ""), 1.0))       # per-section voice trim
            if end - b > 1e-3 and vk > 0: out.append((b, end - b, sc.degree(d, v["octave"] - 1), vk))
        n += 1
    return out


def _shepard(spec, mix, tm, sec, rng):
    """Shepard–Risset riser (chiptune version): 7 octave-spaced partials (G1…G7 of the section key), pulse+triangle,
    Gaussian loudness over log-frequency (centre = key in octave 4, σ ≈ 1.2 oct), stepped one semitone per 16th
    (shepard_rate), each partial wrapping top→bottom inaudibly; crescendo 0→1, hop blips (shepard_hops per beat) that
    follow the steps, thin noise sweep over the last 2 beats. Ends where the section's held breath (stop) begins."""
    from .voices import hz as _hz
    b0 = sec["b0"]; b1 = sec["b1"] - sec["stop"]
    if b1 - b0 <= .25: return
    rate = float(sec.get("shepard_rate", 4)); sig_oct = float(sec.get("shepard_sigma", 1.2))
    t0, t1 = tm.time(b0), tm.time(b1); n = int((t1 - t0) * SR)
    tt = t0 + np.arange(n) / SR
    bb = np.linspace(b0, b1, 256); beat = np.interp(tt, [tm.time(x) for x in bb], bb)
    pos = (beat - b0) * rate; step = np.floor(pos)
    base = 24 + NOTE[_shift_key(sec["key"], sec.get("transpose", 0)).upper()]       # key in octave 1 (G1 = 31)
    centre = base + 36
    y = np.zeros(n)
    for k in range(7):
        m = base + np.mod(12 * k + step, 84)
        amp = np.exp(-.5 * ((m - centre) / (12 * sig_oct)) ** 2)
        ph = np.cumsum(_hz(m)) / SR
        sq = np.where(ph % 1 < .5, .5, -.5); tri = (1 - 4 * np.abs(ph % 1 - .5)); tri = np.round(tri * 7.5) / 7.5
        y += amp * (.55 * sq + .45 * tri * .6)
    frac = pos - step
    art = .62 + .38 * np.exp(-frac * 5)                                     # each chromatic step re-articulates
    cres = np.clip((beat - b0) / (b1 - b0), 0, 1) ** 1.6
    fade = np.clip(np.arange(n) / (.01 * SR), 0, 1) * np.clip((n - np.arange(n)) / (.004 * SR), 0, 1)
    mix.add(t0, y * art * (.08 + .92 * cres) * fade, .085, 0)
    # hop blips: one per 1/hops beat, pitched to the loudest partial of that moment (two octaves up)
    hops = float(sec.get("shepard_hops", 2))
    if hops > 0:
        j = 0
        while b0 + j / hops < b1 - 1e-9:
            hb = b0 + j / hops; st = math.floor((hb - b0) * rate)
            cand = [base + (12 * k + st) % 84 for k in range(7)]; top = min(cand, key=lambda m: abs(m - centre))
            nn = int(.045 * SR); tt_ = np.arange(nn) / SR
            ph = np.cumsum(np.full(nn, float(_hz(top + 12)))) / SR
            blip = np.where(ph % 1 < .125, .5, -.5) * np.exp(-tt_ * 70)
            mix.add(tm.time(hb), blip, .05 * (.4 + .6 * (hb - b0) / (b1 - b0)), .25 * (-1) ** j)
            j += 1
    # thin noise sweep (rising one-pole low-pass) over the last 2 beats
    sb = max(b0, b1 - 2.0); ts = tm.time(sb); ns = int((t1 - ts) * SR)
    if ns > 64:
        from scipy.signal import lfilter
        nz = rng.standard_normal(ns) * .5; out = np.zeros(ns); zi = np.zeros(1); chunks = 24
        for c in range(chunks):
            i0, i1 = c * ns // chunks, (c + 1) * ns // chunks
            a = .04 + .5 * (c / (chunks - 1)) ** 2
            out[i0:i1], zi = lfilter([a], [1, a - 1], nz[i0:i1], zi=zi)
        hp = out - lfilter([.02], [1, -.98], out)                            # keep it thin
        env = (np.arange(ns) / ns) ** 2
        mix.add(ts, hp * env, .16, .15)


def _logo(spec, mix, tm, lb, voices, fl):
    """4-note motif 5→1→2→3 of the CURRENT scale (Hicaz: augmented 2nd), short-short-short-LONG, played by the
    current lead timbre and re-harmonised: bass on the chord root + pad stab of the current chord under the long note."""
    total = spec["total_beats"]
    tb = lb % total if spec.get("loop") and lb >= total else lb
    sec = section_at(spec, min(tb, total - 1e-6))
    sc = Scale(_shift_key(sec["key"], sec.get("transpose", 0)), sec["scale"], sec["tuning"])
    me = Meter(sec["meter"], sec["grouping"])
    cb = max(.5, float(sec["chord_bars"]) * me.bar_beats)
    ch = mkchord(sec["progression"][int((tb - sec["b0"]) // cb) % len(sec["progression"])], sc, 3)
    lead = next((v for v in voices.values() if v["role"] == "lead"), {"type": "pulse", "duty": .25, "vol": .075, "pan": .2, "env": {}})
    o = 5
    notes = [sc.degree(sc.fifth_index(), o - 1), sc.degree(0, o), sc.degree(1, o), sc.degree(2, o)]
    for k, ((off, d), p) in enumerate(zip(LOGO_RHYTHM, notes)):
        b = lb - 1.5 + off
        v = {**lead, "vibrato": .18 if k == 3 else 0, "vib_delay": .15, "env": {"a": .004, "d": .35 if k == 3 else .12, "s": .5, "r": .05}, "echo": 0}
        for bb in ([b] if not spec.get("loop") else [b, b - total] if b >= total else [b]):
            t0 = tm.time(bb); dur = tm.time(bb + d * .95) - t0
            sig = vnote(v, p, dur, None, fl)
            mix.add(t0, sig, .11, .1)
            tri = vnote({"type": "triangle", "env": {"d": .3, "s": .5}}, p - 12, dur, None, fl); mix.add(t0, tri, .12, -.1)
            if k == 3:
                mix.add(tm.time(bb + .75), sig, .04, .5)
                rt = min(ch) - 12
                mix.add(t0, vnote({"type": "triangle", "env": {"d": .6, "s": .6}}, rt, dur, None, fl), .25)
                for cp in ch[:3]:
                    mix.add(t0, vnote({"type": "pulse", "duty": .5, "env": {"a": .01, "d": .5, "s": .3}}, cp + 12, dur, None, fl), .025)
                for i in range(8):
                    sp = vnote({"type": "pulse", "duty": .125, "env": {"d": .03}}, sorted(ch)[i % 3] + 36 + 12 * (i // 3 % 2),
                               tm.time(bb + .125) - tm.time(bb), None, fl)
                    mix.add(tm.time(bb + .5 + i * .125), sp, .03 * (1 - i / 9), .5 * (-1) ** i)


def _chord_degree(ch, sc):
    r = min(ch) % 12
    return min(range(sc.n), key=lambda k: min(abs(((sc.root + sc.steps[k]) - r) % 12), 12 - abs(((sc.root + sc.steps[k]) - r) % 12)))


def _shift_key(key, semis):
    if not semis: return key
    names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    return names[(NOTE[key.upper()] + int(semis)) % 12]


# ------------------------------------------------------------------ io / mastering
def _write(path, st):
    a = (np.clip(st, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.tobytes())


def _read(path):
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32767
        return a.reshape(-1, w.getnchannels())


def loudnorm(src, dst, lufs=-14.0, hf_shelf_db=-3.0, ceiling=.6):
    """Two-pass EBU R128 normalisation (measure, then linear gain) + true-peak safety limiter."""
    import json as _j, re as _re
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"loudnorm=I={lufs}:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    try:
        st = _j.loads(_re.findall(r"\{[^{}]*\}", r.stderr)[-1])
        af = (f"loudnorm=I={lufs}:TP=-1.5:LRA=11:measured_I={st['input_i']}:measured_TP={st['input_tp']}:"
              f"measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}:offset={st['target_offset']}:linear=true")
    except Exception:
        af = f"loudnorm=I={lufs}:TP=-1.5:LRA=11"
    # limiter runs 4× oversampled (catches inter-sample peaks of hard chip edges) and leaves ~4 dB for AAC overshoot (isolated noise-burst SFX ring by ~2.5 dB in the encoder);
    # limiting costs loudness, so a make-up gain before it is re-measured once to land on the target.
    def _render(makeup, ceil=.6):
        # high shelf: full-band LFSR noise (snares, crash/flash SFX) otherwise puts as much energy above 7 kHz as in the
        # presence band; −3 dB there keeps the chip bite but removes the fizz that phone speakers + AAC turn harsh
        shelf = f",highshelf=f=7000:g={hf_shelf_db:.1f}:t=q:w=0.7" if hf_shelf_db else ""
        lim = (f"{shelf},lowpass=f=15500:p=2,volume={makeup:.2f}dB,aresample={SR * 4},alimiter=limit={ceil:.3f}:level=false:attack=1:release=60,"
               f"aresample={SR},alimiter=limit={ceil * 1.05:.3f}:level=false")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af + lim, "-ar", str(SR), "-ac", "2", dst], check=True)
        rr = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", dst, "-af", "ebur128", "-f", "null", "-"],
                            capture_output=True, text=True).stderr
        m_ = _re.findall(r"I:\s+(-?[\d.]+) LUFS", rr)
        return float(m_[-1]) if m_ else lufs
    def _aac_tp():
        """true peak (dBTP) after the delivery codec (AAC 192k): hard chip edges + noise bursts overshoot in the encoder."""
        d = tempfile.mkdtemp(prefix="bitloop_tp_"); m4a = os.path.join(d, "a.m4a")
        try:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", dst, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", m4a], check=True)
            rr = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", m4a, "-af", "ebur128=peak=true", "-f", "null", "-"],
                                capture_output=True, text=True).stderr
            v = _re.findall(r"Peak:\s+(-?[\d.]+) dBFS", rr)
            return float(v[-1]) if v else -99.0
        finally:
            import shutil; shutil.rmtree(d, ignore_errors=True)
    makeup = 0.0; ceil = float(ceiling)              # start ceiling (linear); lowered below if AAC overshoots
    for _ in range(4):                               # loudness on target AND ≤ −1.2 dBTP after AAC (delivery spec −1)
        for _ in range(3):
            got = _render(makeup, ceil)
            if abs(got - lufs) < .3: break
            makeup += (lufs - got) * 1.15
        tp = _aac_tp()
        if tp <= -1.2: break
        ceil *= 10 ** ((-1.4 - tp) / 20)
    return dst


def build_audio(spec, out_wav):
    """Final mastered soundtrack (synth or user file + SFX), loudness-normalised, exactly duration_s long."""
    m = spec["music"]; T = spec["duration_s"]
    tmp = tempfile.mkdtemp(prefix="bitloop_a_")
    if m["source"] == "synth":
        raw = synth(spec, os.path.join(tmp, "raw.wav"))
    else:
        f = m["file"] if os.path.isabs(m["file"]) else os.path.join(spec.get("_dir", "."), m["file"])
        mus = os.path.join(tmp, "mus.wav")
        af = "afade=t=in:d=0.02" + ("" if spec.get("loop") else f",afade=t=out:st={max(0, T - 1.5)}:d=1.5")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(m.get("offset", 0)), "-t", str(T), "-i", f, "-af", af,
                        "-ar", str(SR), "-ac", "2", mus], check=True)
        a = _read(mus)
        if m.get("sfx", True):
            s = _read(synth(spec, os.path.join(tmp, "sfx.wav"), music=False))
            n = min(len(a), len(s)); a = a[:n] * .9 + s[:n] * .5
        a = a / (np.abs(a).max() or 1) * .89
        raw = os.path.join(tmp, "raw.wav"); _write(raw, a)
    loudnorm(raw, out_wav, m.get("lufs", -14), m.get("hf_shelf_db", -3.0), m.get("limit_ceiling", .6))
    import shutil; shutil.rmtree(tmp, ignore_errors=True)          # intermediates only (out_wav lives elsewhere)
    return out_wav
