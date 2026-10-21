"""Narrator text system: full-sentence text blocks, revealed on the music grid.

A block (segment["narration"] = [block, ...]) is a sentence or short paragraph in the 5×7 pixel font:

  text     "Bir kitap *geleceğini* biliyorsa, _sen_ ne seçersin?"   *türkuaz*  _mercan_  \\n = forced break
  at       start beat (segment-relative) or [start, until]         until → else auto (reveal + reading time)
  place    top | dialog | panel | title | mid | callout | world | auto
  size     body (6 px/dot, ≈24 chars/line, ≤5 lines) | head (9, ≈15, ≤3) | title (12, ≈11, ≤3) | int dot
  reveal   type (per letter) | word | line | fade | none
  rate     32nd | 16th | 8th | beat | half | auto | <beats>   (one unit per step, steps on the beat grid)
  blip     true | false | {"every": 2, "vol": 1.0}             soft chiptune blip on the same steps (SFX 'blip')
  cursor   (type default true) block cursor, blinks on 8ths once complete
  hold     extra seconds after the reading time               exit  dither | wipe | cut   exit_beats
  case     as_is | upper (Turkish-aware)
  speaker  dialog name tab        target/side  callout pointer ([x, y] world or "focus")
  surface  world: {"x","y","w","dot","rot","fill","ink"} in scene coordinates
  xy       explicit [fx, fy] screen fraction of the block centre (overrides placement)

Everything lands on one clock: units appear at start + lead + step·rate (beats → tempo map), the SFX
blips are timeline events at exactly those beats, and the validator reads the same timings."""
import math, re
import numpy as np
from .pixfont import GLYPHS, norm, missing as _font_missing
from .palette import BAYER4

# ------------------------------------------------------------------ legibility (measured, see min_legible_dot)
# Smallest current phone (5.4", 19.5:9 → 124.4 mm tall screen) held at 35 cm. ISO 9241-303 / ANSI-HFES 100
# ask for ≥ 20–22 arcmin character (cap) height for comfortable reading (16′ = absolute minimum).
PHONE = {"screen_h_mm": 124.4, "dist_mm": 350.0}
MIN_ARCMIN = 22.0
MIN_DOT = 5                       # = min_legible_dot(); asserted in tests/test_narration.py
SIZES = {"body": 6, "head": 9, "title": 12}
MAX_LINES = {"body": 5, "head": 3, "title": 3}
PITCH = 12                         # dots per line: 10-row glyph cell (accents + descender) + 2 rows leading
READ = {"per_word": .35, "base": .6}   # seconds a fully revealed block must stay readable
SAFE = {"top": .05, "bottom": .18, "left": .05, "right": .125}   # platform UI: caption/buttons/action column
RATES = {"32nd": .125, "16th": .25, "8th": .5, "triplet": 1 / 3, "beat": 1.0, "4th": 1.0, "half": 2.0}
AUTO_RATES = {"type": ["16th", "32nd"], "word": ["beat", "8th", "16th"], "line": ["half", "beat", "8th"]}
PLACES = ("top", "dialog", "panel", "title", "mid", "callout", "world", "auto")
REVEALS = ("type", "word", "line", "fade", "none")
EXITS = ("dither", "wipe", "cut")
VOWELS = set("aeıioöuüâîûAEIİOÖUÜÂÎÛ")
DEFAULTS = {"place": "auto", "size": None, "reveal": "type", "rate": "auto", "blip": True, "cursor": None,
            "hold": 0.0, "exit": "dither", "exit_beats": .5, "enter_beats": .25, "case": "as_is", "pauses": True}
TEST_CHARS = "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZabcçdefgğhıijklmnoöprsştuüvyz0123456789.,!?%"


def cap_arcmin(dot, H=1920, screen_h_mm=PHONE["screen_h_mm"], dist_mm=PHONE["dist_mm"]):
    """Visual angle (arcmin) of the 7-dot cap height at `dot` output px per font dot."""
    h = 7 * dot * screen_h_mm / H
    return math.degrees(2 * math.atan(h / 2 / dist_mm)) * 60


def recognition(dot, out_w=720, W=1080, blur=.6, jpeg=40, chars=TEST_CHARS):
    """Simulated phone read: each glyph (cream on navy) at `dot`, downscaled to a 720p stream, display blur and
    JPEG-40 compression, then nearest-template classification against clean glyphs at the same scale.
    → (accuracy, worst margin)."""
    from PIL import Image, ImageFilter
    import io
    s = out_w / W
    def img(ch, degrade):
        g = np.pad(GLYPHS[ch], 1).astype(np.float32)
        big = np.kron(g, np.ones((dot, dot), np.float32))
        im = Image.fromarray((big * 200 + 20).astype(np.uint8))
        im = im.resize((max(1, round(big.shape[1] * s)), max(1, round(big.shape[0] * s))), Image.BILINEAR)
        if degrade:
            im = im.filter(ImageFilter.GaussianBlur(blur))
            if jpeg:
                b = io.BytesIO(); im.save(b, "JPEG", quality=jpeg); im = Image.open(io.BytesIO(b.getvalue())).convert("L")
        return np.asarray(im, np.float32).ravel() / 255
    cs = [c for c in dict.fromkeys(chars) if c in GLYPHS]
    T = np.stack([img(c, False) for c in cs])
    ok, margin = 0, 1e9
    for i, c in enumerate(cs):
        d = np.abs(T - img(c, True)).sum(1)
        j = np.argsort(d)
        ok += j[0] == i
        margin = min(margin, (d[j[1]] - d[i]) / max(d[j[1]], 1e-6))
    return ok / len(cs), float(margin)


def min_legible_dot(lo=2, hi=12):
    """Smallest dot passing BOTH the visual-angle rule and 100 % simulated recognition."""
    for d in range(lo, hi + 1):
        if cap_arcmin(d) >= MIN_ARCMIN and recognition(d)[0] == 1.0: return d
    return hi


PAD_X = {"dialog": 7}
PAD_Y = {"dialog": 5, "callout": 3}


def dot_px(size, W=1080):
    d = SIZES.get(size, size) if isinstance(size, str) else size
    return max(1, int(round(float(d) * W / 1080)))


def safe_rect(W, H):
    return (round(W * SAFE["left"]), round(H * SAFE["top"]), W - round(W * SAFE["right"]), H - round(H * SAFE["bottom"]))


# ------------------------------------------------------------------ Turkish text: markup, words, wrapping
def tr_upper(text):
    return text.replace("i", "İ").replace("ı", "I").upper()


def parse(text):
    """→ list of (char, colour) with colour 0 = text, 1 = highlight (*…*), 2 = second highlight (_…_)."""
    out = []
    for p in re.split(r"(\*[^*\n]+\*|_[^_\n]+_)", text):
        if not p: continue
        c = 1 if p[0] == "*" and p[-1] == "*" and len(p) > 2 else 2 if p[0] == "_" and p[-1] == "_" and len(p) > 2 else 0
        out += [(ch, c) for ch in (p[1:-1] if c else p)]
    return out


def _gw(ch): return GLYPHS.get(ch, GLYPHS["?"]).shape[1]
def word_w(w): return sum(_gw(" " if c == "\u00a0" else c) for c, _ in w) + max(0, len(w) - 1)
SPACE = 5                                    # 1 gap + 3-wide space + 1 gap


def words(chars):
    """Split parsed chars into ['w', [(ch, col)…]] / ['br'] items, applying Turkish non-breaking joins:
    digit groups (300 000), number + unit/short word (10 km, %40, 3 sn), so they never split across lines."""
    items, cur = [], []
    for ch, c in chars:
        if ch == "\n":
            if cur: items.append(["w", cur]); cur = []
            items.append(["br"])
        elif ch == " ":
            if cur: items.append(["w", cur]); cur = []
        else: cur.append((norm(ch) if ch != "\u00a0" else ch, c))
    if cur: items.append(["w", cur])
    # expand aliases that became multi-char (… → ...)
    for it in items:
        if it[0] == "w": it[1] = [(x, c) for s, c in it[1] for x in s]
    out = []
    for it in items:
        if it[0] == "w" and out and out[-1][0] == "w":
            prev = "".join(x for x, _ in out[-1][1]); this = "".join(x for x, _ in it[1])
            num_group = prev[-1:].isdigit() and (this[:1].isdigit() or (this.isalpha() and len(this) <= 3) or this[:1] in "%°")
            if num_group and len(this.strip(".,!?;:")) <= 4:
                out[-1][1] = out[-1][1] + [("\u00a0", 0)] + it[1]; continue
        out.append(it)
    return out


def syllable_breaks(w):
    """Indices where a Turkish word may be hyphenated (each syllable has one vowel; a single consonant between
    vowels starts the next syllable, of a consonant cluster only the last one does: ka-lem, kit-ap→ki-tap, türk-çe)."""
    s = [ch for ch, _ in w]; vi = [i for i, ch in enumerate(s) if ch in VOWELS]
    out = []
    for a, b in zip(vi, vi[1:]):
        k = b if b - a == 1 else b - 1      # vowel-vowel: break between them; else before the last consonant
        if 2 <= k <= len(s) - 2: out.append(k)
    return out


def _is_short(w):
    t = "".join(c for c, _ in w).strip(".,!?;:")
    return t.isalpha() and len(t) <= 2


def wrap(items, maxw):
    """Greedy Turkish wrap in dots → list of lines, each a list of words (list of (ch, col)). Never breaks inside a
    word unless it alone exceeds the width (then syllable hyphenation); avoids 1–2-letter words at line ends."""
    lines, cur, cw = [], [], 0
    seq = list(items)
    i = 0
    def push():
        nonlocal cur, cw
        lines.append(cur); cur, cw = [], 0
    while i < len(seq):
        it = seq[i]; i += 1
        if it[0] == "br":
            push(); continue
        w = it[1]; ww = word_w(w)
        need = ww if not cur else cw + SPACE + ww
        if need <= maxw:
            nxt = seq[i][1] if i < len(seq) and seq[i][0] == "w" else None
            if cur and nxt is not None and _is_short(w) and need + SPACE + word_w(nxt) > maxw and ww + SPACE + word_w(nxt) <= maxw:
                push(); cur, cw = [w], ww; continue
            cur.append(w); cw = need; continue
        if ww <= maxw:
            push(); cur, cw = [w], ww; continue
        # over-long word: hyphenate at the latest syllable break that fits (into the current line if possible)
        room = maxw - (cw + SPACE if cur else 0)
        cuts = [k for k in syllable_breaks(w) if word_w(w[:k] + [("-", 0)]) <= room]
        if not cuts and cur:
            push(); room = maxw; cuts = [k for k in syllable_breaks(w) if word_w(w[:k] + [("-", 0)]) <= room]
        if not cuts:                                        # no syllable fits: hard cut by width
            k = 1
            while k < len(w) and word_w(w[:k + 1] + [("-", 0)]) <= room: k += 1
            cuts = [k]
        k = cuts[-1]; head = w[:k] + [("-", 0)]
        cur.append(head); cw = (cw + SPACE if len(cur) > 1 else 0) + word_w(head)
        push(); seq.insert(i, ["w", w[k:]])
    if cur or not lines: push()
    return [l for l in lines if l] or [[]]


def line_w(line): return sum(word_w(w) for w in line) + SPACE * max(0, len(line) - 1)


def balanced(items, maxw):
    """Same number of lines as greedy wrap, but the narrowest width that keeps it (even, title-like lines)."""
    base = wrap(items, maxw); n = len(base); lo, hi = 1, maxw
    while lo < hi:
        m = (lo + hi) // 2; r = wrap(items, m)
        if len(r) <= n and all(line_w(l) <= m for l in r): hi = m
        else: lo = m + 1
    out = wrap(items, lo)
    return out if len(out) == n else base


def word_count(text):
    return len([w for w in re.sub(r"[*_]", "", text).replace("\n", " ").split() if any(ch.isalnum() for ch in w)])


# ------------------------------------------------------------------ blocks: normalise + timing (pure, no Film)
def normalise_block(b, defaults=None):
    b = {"text": b} if isinstance(b, str) else dict(b)
    for k, v in {**DEFAULTS, **(defaults or {})}.items(): b.setdefault(k, v)
    if b["place"] == "title" and b["size"] is None: b["size"] = "title"
    if b["place"] == "world": b.setdefault("surface", {})
    if b["size"] is None: b["size"] = "body"
    if b["cursor"] is None: b["cursor"] = b["reveal"] == "type" and b["place"] not in ("world", "title")
    at = b.get("at", 0)
    if isinstance(at, (list, tuple)): b["at"], b["until"] = float(at[0]), at[1]
    else: b["at"] = float(at)
    return b


def layout_dims(b, W=1080, H=1920):
    """→ (dot px, max text width in dots, align) for a block (world: dots of the surface)."""
    x0, _, x1, _ = safe_rect(W, H); sw = x1 - x0
    if b["place"] == "world":
        sf = b.get("surface") or {}; d = float(sf.get("dot", 1.0))
        return d, int(sf.get("w", 120) / d), sf.get("align", "center")
    dot = dot_px(b["size"], W)
    pad = PAD_X.get(b["place"], 5)
    if b.get("width"): maxw = int(b["width"]) * 6 - 1
    elif b["place"] == "callout": maxw = 14 * 6 - 1
    else: maxw = sw // dot - 2 * pad
    maxw = min(maxw, sw // dot - 2 * pad)
    align = b.get("align") or ("center" if b["place"] in ("top", "title", "mid", "auto") else "left")
    return dot, maxw, align


def block_lines(b, W=1080, H=1920):
    txt = norm(b["text"]).replace("\\n", "\n")
    if b.get("case") == "upper": txt = tr_upper(txt)
    items = words(parse(txt)); dot, maxw, align = layout_dims(b, W, H)
    lines = balanced(items, maxw) if align == "center" and b["place"] != "world" else wrap(items, maxw)
    return lines, dot, maxw, align


def units(b, lines):
    """Reveal order → list of per-char (line, word, ci, step) + n_steps. Pauses: +1 step after , ; : and +2
    after . ! ? (only between units) so sentences breathe on the grid."""
    out, step = [], 0
    mode = b["reveal"]
    allw = [(li, wi, w) for li, l in enumerate(lines) for wi, w in enumerate(l)]
    for n, (li, wi, w) in enumerate(allw):
        last_w = n == len(allw) - 1
        if mode == "line" and n and allw[n - 1][0] != li: step += 1
        for ci, (ch, _) in enumerate(w):
            if mode == "type" and ch in "-\u00a0" and ci: out.append((li, wi, ci, max(step - 1, 0))); continue
            out.append((li, wi, ci, step if mode in ("type", "word", "line") else 0))
            if mode == "type": step += 1
        tail = w[-1][0] if w else ""
        if mode == "word" and not last_w: step += 1
        if b.get("pauses") and mode in ("type", "word") and not last_w:
            step += 2 if tail in ".!?" else 1 if tail in ",;:" else 0
    n_steps = (max(u[3] for u in out) + 1) if out else 1
    if mode == "type": n_steps = (out[-1][3] + 1) if out else 1
    return out, n_steps


def _rate(name):
    return RATES[name] if isinstance(name, str) else float(name)


def timing(b, g, tm, n_steps, total_beats, per_word=READ["per_word"], base=READ["base"]):
    """Resolve rate/lead/until for a block of segment g → dict of beats & seconds."""
    seg0, seg1 = g["start_beat"], g["end_beat"]
    start = seg0 + b["at"]; mode = b["reveal"]
    nw = word_count(b["text"]); read_s = base + per_word * nw + float(b.get("hold") or 0)
    if b.get("until") not in (None, "auto"):
        hard_end = seg1 if b["until"] == "segment" else seg0 + float(b["until"])
    else: hard_end = None
    avail_end = hard_end if hard_end is not None else seg1
    ex = 0.0 if b["exit"] == "cut" else float(b["exit_beats"])
    def plan(rate):
        lead = rate if mode == "type" else 0.0
        full = start + lead + (n_steps - 1) * rate if mode in ("type", "word", "line") else start + (1.0 if mode == "fade" else 0)
        if hard_end is not None: end = hard_end
        else:
            et = tm.time(full) + read_s; end = math.ceil((float(tm.beat(et)) + ex) * 2 - 1e-6) / 2
            end = min(end, avail_end)
        end = min(end, total_beats)
        ok = tm.time(end - ex) - tm.time(full) >= read_s - 1e-6
        return dict(rate=rate, lead=lead, start=start, full=full, end=end, exit0=end - ex, read_s=read_s, words=nw, ok=ok)
    if mode not in ("type", "word", "line"): return plan(0.0)
    if b["rate"] == "auto":
        ps = [plan(_rate(r)) for r in AUTO_RATES[mode]]
        p = next((p for p in ps if p["ok"]), ps[-1])
    else: p = plan(_rate(b["rate"]))
    return p


def blip_events(b, lines, U, p):
    """[(beat, kind)] — one soft blip every `every` letters (vowels a little higher) / per word / per line."""
    bl = b.get("blip")
    if not bl or b["reveal"] not in ("type", "word", "line"): return []
    every = int(bl.get("every", 2 if b["reveal"] == "type" else 1)) if isinstance(bl, dict) else (2 if b["reveal"] == "type" else 1)
    vol = float(bl.get("vol", 1.0)) if isinstance(bl, dict) else 1.0
    suf = "" if abs(vol - 1) < 1e-6 else f"@{vol:g}"
    ev, seen, k = [], set(), 0
    for li, wi, ci, st in U:
        if st in seen: continue
        seen.add(st); ch = lines[li][wi][ci][0]
        if ch in "-\u00a0": continue
        if k % every == 0:
            ev.append((p["start"] + p["lead"] + st * p["rate"], ("blip_hi" if ch in VOWELS else "blip") + suf))
        k += 1
    return ev


def blocks(spec):
    """All narration blocks of a normalised spec, laid out (wrap) and timed. Pure function of the spec."""
    from .timing import tempo_map
    tm = tempo_map(spec); f = spec["format"]; W, H = f["width"], f["height"]
    rd = {**READ, **(spec.get("readability") or {})}
    out = []
    for gi, g in enumerate(spec["segments"]):
        for bi, b in enumerate(g.get("narration") or []):
            b = dict(b)
            lines, dot, maxw, align = block_lines(b, W, H)
            U, n = units(b, lines)
            p = timing(b, g, tm, n, spec["total_beats"], rd["per_word"], rd["base"])
            out.append({"seg": gi, "sid": g["id"], "i": bi, "b": b, "lines": lines, "dot": dot, "maxw": maxw, "align": align,
                        "units": U, "n_steps": n, "t": p, "blips": blip_events(b, lines, U, p),
                        "t0": tm.time(p["start"]), "t_full": tm.time(p["full"]), "t_exit": tm.time(p["exit0"]),
                        "t1": tm.time(p["end"])})
    return out


def missing(text, case="as_is"):
    t = re.sub(r"[*_]", "", text)
    return _font_missing(tr_upper(t) if case == "upper" else t)


# ------------------------------------------------------------------ rasterising a block (dot space)
C_BOX, C_TEXT, C_HI, C_HI2, C_BORDER, C_ACCENT, C_RULE = 1, 2, 3, 4, 5, 6, 7


def raster(B):
    """Dot-space block image: colour ids C, unit-step map S (−1 = not text), cursor slots, box geometry."""
    b, lines, align = B["b"], B["lines"], B["align"]
    place = b["place"]; world = place == "world"
    # the cursor (4 dots + 1 gap) overhangs into the ≥ 5-dot side padding, so it costs no line width
    pad_x, pad_y = (0, 0) if world else (PAD_X.get(place, 5), PAD_Y.get(place, 3))
    lw = [line_w(l) for l in lines]; tw = max(lw + [1])
    if world: tw = max(tw, B["maxw"]) if (b.get("surface") or {}).get("fill") else tw
    if place == "panel": tw = max(tw, B["maxw"])
    nl = len(lines); th = nl * PITCH - 2
    w, h = tw + 2 * pad_x, th + 2 * pad_y
    C = np.zeros((h, w), np.uint8); S = np.full((h, w), -1, np.int32)
    if not world or (b.get("surface") or {}).get("fill"):
        C[:] = C_BOX
    if place == "dialog":
        C[0, :] = C[-1, :] = C_BORDER; C[:, 0] = C[:, -1] = C_BORDER
        C[2, 2:-2] = C[-3, 2:-2] = C_ACCENT; C[2:-2, 2] = C[2:-2, -3] = C_ACCENT
    if place == "callout":
        C[0, :] = C[-1, :] = C_ACCENT; C[:, 0] = C[:, -1] = C_ACCENT
    if place == "title":
        C[-2, pad_x:w - pad_x] = C_RULE
    if place == "panel":                       # opaque band, Türkuaz rule on top, a dithered fringe below
        C[0, :] = C_ACCENT
    step_of = {}
    for li, wi, ci, st in B["units"]: step_of[(li, wi, ci)] = st
    slots = {}                                # step → (x_after, y_top) for the cursor
    for li, l in enumerate(lines):
        x = pad_x + (0 if align == "left" else (tw - lw[li]) // 2)
        y = pad_y + li * PITCH
        for wi, wd in enumerate(l):
            for ci, (ch, col) in enumerate(wd):
                g = GLYPHS.get(" " if ch == "\u00a0" else ch, GLYPHS["?"]); gw = g.shape[1]
                st = step_of.get((li, wi, ci), 0)
                reg = (slice(y, y + 10), slice(x, x + gw))
                C[reg][g] = C_TEXT + col; S[reg][g] = st
                slots[st] = (x + gw + 1, y)
                x += gw + 1
            x += SPACE - 1
    return {"C": C, "S": S, "slots": slots, "pad": (pad_x, pad_y), "w": w, "h": h}


def _bay(h, w):
    return np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]


def state(B, beat):
    """Reveal state at an absolute beat → (k_enter, k_exit, visible step count, done?)."""
    p, b = B["t"], B["b"]
    if beat < p["start"] or beat > p["end"]: return None
    ke = 1.0 if b.get("_no_enter") else min(1.0, (beat - p["start"]) / max(b["enter_beats"], 1e-6))
    kx = 0.0 if b["exit"] == "cut" or beat < p["exit0"] else min(1.0, (beat - p["exit0"]) / max(p["end"] - p["exit0"], 1e-6))
    if b.get("_frozen") is not None: n = b["_frozen"]
    elif b["reveal"] in ("type", "word", "line"): n = int(math.floor((beat - p["start"] - p["lead"]) / p["rate"] + 1e-6)) + 1
    else: n = B["n_steps"]
    return ke, kx, max(0, min(n, B["n_steps"])), beat >= p["full"] - 1e-6


def paint(B, R, beat, colors):
    """→ (RGBA dot image or None). colors: dict id→(r,g,b) uint8."""
    st = state(B, beat)
    if st is None: return None
    ke, kx, n, done = st; b = B["b"]
    C, S = R["C"], R["S"]; h, w = C.shape
    bay = R.setdefault("bay", _bay(h, w))
    text = (S >= 0) & (S < n)
    if b["reveal"] == "fade":
        text &= bay < min(1.0, (beat - B["t"]["start"]) / 1.0 * 1.4)
    keep = np.ones((h, w), bool)
    if kx > 0:
        if b["exit"] == "wipe": keep = np.arange(w)[None, :] >= int(round(kx * w))
        else: keep = bay >= kx
    has_box = b["place"] != "world" or (b.get("surface") or {}).get("fill")
    box = ((C > 0) & ((S < 0) | (S >= n))) if has_box else np.zeros((h, w), bool)
    box &= (bay < ke * 1.05) & keep
    text &= keep
    rgba = np.zeros((h, w, 4), np.uint8)
    for cid in np.unique(C[box]):
        m = box & (C == cid)
        col = colors[C_BOX] if cid in (C_TEXT, C_HI, C_HI2) else colors[int(cid)]
        rgba[m, :3] = col; rgba[m, 3] = 255
    for cid in (C_TEXT, C_HI, C_HI2):
        m = text & (C == cid); rgba[m, :3] = colors[cid]; rgba[m, 3] = 255
    o = None
    if b["place"] == "world" and not (b.get("surface") or {}).get("fill"):
        o = np.zeros_like(text); o[1:] |= text[:-1]; o[:-1] |= text[1:]; o[:, 1:] |= text[:, :-1]; o[:, :-1] |= text[:, 1:]
        o &= ~text & keep
        if (b.get("surface") or {}).get("outline", True):
            rgba[o, :3] = colors[C_BOX]; rgba[o, 3] = 255
    blink_on = int(math.floor((beat - B["t"]["full"]) * 2)) % 2 == 0
    if b["cursor"] and kx == 0 and n > 0 and (not done or blink_on):
        ks = R.setdefault("keys", sorted(R["slots"]))
        j = int(np.searchsorted(ks, n - 1, side="right")) - 1
        x, y = R["slots"][ks[j]] if j >= 0 else (R["pad"][0], R["pad"][1])
        rgba[y + 2:y + 9, x:x + 4, :3] = colors[C_HI]; rgba[y + 2:y + 9, x:x + 4, 3] = 255
    if b["place"] == "dialog" and done and kx == 0 and blink_on:
        x, y = w - 10, h - 9
        for r, (a, c) in enumerate(((0, 5), (1, 4), (2, 3))):
            rgba[y + r, x + a:x + c, :3] = colors[C_HI]; rgba[y + r, x + a:x + c, 3] = 255
    return rgba


def speaker_tab(name, colors):
    from .pixfont import line_bitmap
    m, _ = line_bitmap([(name, False)])
    h, w = 14, m.shape[1] + 6
    rgba = np.zeros((h, w, 4), np.uint8); rgba[..., :3] = colors[C_BOX]; rgba[..., 3] = 255
    rgba[0, :, :3] = colors[C_BORDER]; rgba[:, 0, :3] = colors[C_BORDER]; rgba[:, -1, :3] = colors[C_BORDER]
    reg = rgba[2:12, 3:3 + m.shape[1]]; reg[m, :3] = colors[C_HI]
    return rgba


# ------------------------------------------------------------------ the track (layout + compositing, uses Film)
def _overlap(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


class NarrationTrack:
    """All narration blocks of a Film: auto-layout (safe zones, subject bbox, other text) + per-frame compositing."""
    PREF = {"top": 0.0, "dialog": .08, "mid": .2}

    def __init__(self, film, caption_rects=()):
        self.f = film; s = film.s; self.W, self.H, self.g = film.W, film.H, film.g
        cap = film.pal.caption
        self.colors = {C_BOX: cap["box"], C_TEXT: cap["text"], C_HI: cap["hi"], C_HI2: cap.get("hi2", cap["hi"]),
                       C_BORDER: cap["text"], C_ACCENT: cap["hi"], C_RULE: cap.get("hi2", cap["hi"])}
        self.blocks = blocks(s); self.report = []
        self.safe = safe_rect(self.W, self.H)
        occupied = list(caption_rects)          # (t0, t1, rect)
        for B in self.blocks:
            B["R"] = raster(B)
            if B["b"]["place"] == "world": continue
            self._place(B, occupied)
            occupied.append((B["t0"], B["t1"], B["rect"]))
        # loop return: the film's first block re-appears (frozen at its frame-0 state) so frame T == frame 0
        if s.get("loop") and self.blocks:
            B0 = self.blocks[0]
            if B0["seg"] == 0 and B0["t"]["start"] <= 1e-6 and B0["b"]["place"] != "world":
                B0["b"]["_no_enter"] = True
                n0 = state(B0, 0.0)[2]
                tb = s["total_beats"]; lb = s.get("loop_beats", 2.0) * .5
                p = dict(B0["t"], start=tb - lb, end=tb + 99, exit0=tb + 99, full=tb + 99)
                bb = dict(B0["b"], _frozen=n0, exit="cut", _no_enter=B0["b"].get("_no_enter"), enter_beats=lb)
                self.blocks.append(dict(B0, b=bb, t=p, blips=[], t0=film.tm.time(tb - lb), t1=film.T + 1, _loop=True))

    # --- geometry
    def subject_rect(self, i, lb):
        f = self.f; g = f.s["segments"][i]; dur = g["end_beat"] - g["start_beat"]
        sub = g.get("subject")
        if sub == "none": return None
        cv = f.cv2; cv.set_cam(f.camera(i, lb))
        if isinstance(sub, (list, tuple)) and len(sub) == 4: x0, y0, x1, y1 = sub
        else:
            fx, fy = f.scenes[i].focus(lb, dur); r = float(sub) if isinstance(sub, (int, float)) else 40.0
            x0, y0, x1, y1 = fx - r, fy - r, fx + r, fy + r
        xs, ys = cv.to_screen(np.array([x0, x1, x0, x1]), np.array([y0, y0, y1, y1]))
        return (float(xs.min()) * self.g, float(ys.min()) * self.g, float(xs.max()) * self.g, float(ys.max()) * self.g)

    def world_px(self, i, t, x, y):
        f = self.f; lb = f._lb(i, t); f.cv2.set_cam(f.camera(i, lb)); X, Y = f.cv2.to_screen(x, y)
        return float(X) * self.g + self.g / 2, float(Y) * self.g + self.g / 2

    def _subjects(self, B):
        i = B["seg"]; g = self.f.s["segments"][i]; out = []
        for q in (0.0, .5, 1.0):
            t = B["t0"] + (B["t1"] - B["t0"]) * q
            r = self.subject_rect(i, self.f._lb(i, min(t, g["end_s"] - 1e-3)))
            if r: out.append(r)
        return out

    def _rect_at(self, B, place, cx=None, cy=None, top=None, bottom=None):
        d = B["dot"]; R = B["R"]; w, h = R["w"] * d, R["h"] * d
        x0, y0, x1, y1 = self.safe; g = self.g
        if place == "panel": cx = (x0 + x1) / 2
        if cx is None: cx = (x0 + x1) / 2
        x = int(round(cx - w / 2)); x = max(x0, min(x, x1 - w))
        if top is not None: y = top
        elif bottom is not None: y = bottom - h
        else: y = int(round(cy - h / 2))
        y = max(y0, min(y, y1 - h))
        x -= x % g; y -= y % g
        return (x, y, x + w, y + h)

    def _cand(self, B, place):
        H = self.H; x0, y0, x1, y1 = self.safe
        if place == "top": return self._rect_at(B, place, top=int(H * 186 / 1920))
        if place in ("dialog", "panel"): return self._rect_at(B, place, bottom=y1 - 12)
        if place == "title": return self._rect_at(B, place, cy=H * .40)
        if place == "mid": return self._rect_at(B, place, cy=H * .42)
        raise ValueError(place)

    def _place(self, B, occupied):
        b = B["b"]; place = b["place"]; d = B["dot"]
        busy = [r for t0, t1, r in occupied if t0 < B["t1"] and B["t0"] < t1]
        subs = self._subjects(B)
        area = max(1, B["R"]["w"] * d * B["R"]["h"] * d)
        if b.get("xy"):
            fx, fy = b["xy"]; B["rect"] = self._rect_at(B, place, cx=fx * self.W, cy=fy * self.H)
        elif place == "callout":
            B["rect"] = self._callout(B, subs, busy)
        elif place == "auto":
            best = None
            for pl in ("top", "dialog", "mid"):
                r = self._stack(self._cand(B, pl), busy, pl)
                cost = sum(_overlap(r, s) for s in subs) / area / max(1, len(subs)) + 2 * sum(_overlap(r, o) for o in busy) / area + self.PREF[pl]
                if best is None or cost < best[0] - 1e-9: best = (cost, r, pl)
            B["rect"], B["placed"] = best[1], best[2]
        else:
            B["rect"] = self._stack(self._cand(B, place), busy, place)
        B.setdefault("placed", place)
        r = B["rect"]
        if "{{" in b["text"]: B["subject_cover"] = 0; return
        cov = max((_overlap(r, s) / area for s in subs), default=0)
        B["subject_cover"] = cov
        if cov > .3 and place not in ("callout",): self.report.append(f"{B['sid']}: narration block {B['i'] + 1} covers {cov:.0%} of the subject (move it / set 'place')")
        x0, y0, x1, y1 = self.safe
        if r[0] < x0 - 1 or r[2] > x1 + 1 or r[1] < y0 - 1 or r[3] > y1 + 1:
            self.report.append(f"{B['sid']}: narration block {B['i'] + 1} leaves the UI-safe area")
        if any(_overlap(r, o) > 0 for o in busy): self.report.append(f"{B['sid']}: narration block {B['i'] + 1} overlaps other text")

    def _stack(self, r, busy, place):
        for _ in range(6):
            hit = [o for o in busy if _overlap(r, o) > 0]
            if not hit: return r
            h = r[3] - r[1]
            if place in ("dialog", "panel"): y = min(o[1] for o in hit) - 18 - h
            else: y = max(o[3] for o in hit) + 18
            y -= y % self.g
            r = (r[0], y, r[2], y + h)
        return r

    def _target(self, B, t):
        b = B["b"]; i = B["seg"]; tg = b.get("target", "focus")
        if tg == "focus" or tg is None:
            g = self.f.s["segments"][i]; lb = self.f._lb(i, t); x, y = self.f.scenes[i].focus(lb, g["end_beat"] - g["start_beat"])
        else: x, y = tg
        return self.world_px(i, min(t, self.f.s["segments"][i]["end_s"] - 1e-3), x, y)

    def _callout(self, B, subs, busy):
        d = B["dot"]; w, h = B["R"]["w"] * d, B["R"]["h"] * d
        tx, ty = self._target(B, B["t0"]); gap = 90
        side = B["b"].get("side")
        opts = {"right": (tx + gap + w / 2, ty), "left": (tx - gap - w / 2, ty), "above": (tx, ty - gap - h / 2), "below": (tx, ty + gap + h / 2)}
        order = [side] if side in opts else list(opts)
        best = None
        for k in order:
            r = self._rect_at(B, "callout", cx=opts[k][0], cy=opts[k][1])
            on_target = r[0] <= tx <= r[2] and r[1] <= ty <= r[3]
            cost = (2 * sum(_overlap(r, o) for o in busy) + 1.5 * sum(_overlap(r, o) for o in (subs or []))) / (w * h) \
                + (5 if on_target else 0) + math.hypot((r[0] + r[2]) / 2 - tx, (r[1] + r[3]) / 2 - ty) / self.H
            if best is None or cost < best[0]: best = (cost, r)
        return best[1]

    # --- per frame
    def composite(self, out, t):
        beat = float(self.f.tm.beat(min(t, self.f.T))) if t <= self.f.T else self.f.s["total_beats"] + (t - self.f.T) / self.f.beat
        for B in self.blocks:
            if B["b"]["place"] == "world" or not (B["t0"] - 1e-6 <= t <= B["t1"] + 1e-6): continue
            img = paint(B, B["R"], beat, self.colors)
            if img is None: continue
            d = B["dot"]; x, y = B["rect"][:2]
            if B["b"]["place"] == "callout": self._leader(out, B, t, beat)
            if B["b"].get("speaker") and B["b"]["place"] == "dialog":
                tab = speaker_tab(B["b"]["speaker"], self.colors)
                st = state(B, beat)
                if st and st[0] >= 1 and st[1] == 0: self._paste(out, tab, x + 4 * d, y - (tab.shape[0] - 1) * d, d)
            self._paste(out, img, x, y, d)
        return out

    def _paste(self, out, img, x, y, d):
        big = np.repeat(np.repeat(img, d, 0), d, 1)
        H, W = out.shape[:2]
        xa, ya, xb, yb = max(0, x), max(0, y), min(W, x + big.shape[1]), min(H, y + big.shape[0])
        if xa >= xb or ya >= yb: return
        sub = big[ya - y:yb - y, xa - x:xb - x]; m = sub[..., 3] > 0
        out[ya:yb, xa:xb][m] = sub[..., :3][m]

    def _leader(self, out, B, t, beat):
        st = state(B, beat)
        if not st or st[1] > .5: return
        r = B["rect"]; tx, ty = self._target(B, t); g = self.g
        cx = min(max(tx, r[0]), r[2]); cy = min(max(ty, r[1]), r[3])
        if r[0] < tx < r[2]: cy = r[1] if ty < r[1] else r[3]
        else: cx = r[0] if tx < r[0] else r[2]
        k = st[0]; ex, ey = cx + (tx - cx) * k, cy + (ty - cy) * k
        n = int(max(abs(ex - cx), abs(ey - cy)) / g) + 1
        H, W = out.shape[:2]
        def sq(X, Y, s, col):
            X, Y = int(X // g * g), int(Y // g * g)
            out[max(0, Y - s):min(H, Y + g + s), max(0, X - s):min(W, X + g + s)] = col
        pts = [(cx + (ex - cx) * q / max(n, 1), cy + (ey - cy) * q / max(n, 1)) for q in range(n + 1)]
        for X, Y in pts: sq(X, Y, g // 2, self.colors[C_BOX])
        for X, Y in pts: sq(X, Y, 0, self.colors[C_TEXT])
        if k >= 1:
            sq(tx, ty, g, self.colors[C_BOX]); sq(tx, ty, g // 2, self.colors[C_HI])

    def draw_world(self, cv, i, t):
        """In-world blocks (sign, screen, book page, chalkboard): drawn in art space inside the scene."""
        from .bitmap import Bitmap, draw_bitmap
        beat = float(self.f.tm.beat(t))
        for B in self.blocks:
            if B["seg"] != i or B["b"]["place"] != "world": continue
            img = paint(B, B["R"], beat, self.colors)
            if img is None: continue
            sf = B["b"].get("surface") or {}; d = float(sf.get("dot", 1.0))
            x, y, rot = float(sf.get("x", 0)), float(sf.get("y", 0)), float(sf.get("rot", 0))
            ink = sf.get("ink")
            for col in {tuple(c) for c in img[img[..., 3] > 0][:, :3].tolist()}:
                m = (img[..., 3] > 0) & np.all(img[..., :3] == col, -1)
                c = np.asarray(col, np.float32) / 255
                if ink == "dark" and col == tuple(self.colors[C_TEXT]): c = np.asarray(self.colors[C_BOX], np.float32) / 255
                draw_bitmap(cv, Bitmap(m, x, y, d, rot), c, 1.0, snap=True)

    def world_screen_dot(self, B):
        """Smallest on-screen px per font dot of a world block over its window (camera zoom × grid)."""
        i = B["seg"]; f = self.f; d = float((B["b"].get("surface") or {}).get("dot", 1.0)); z = 1e9
        for q in np.linspace(0, 1, 5):
            t = B["t0"] + (B["t1"] - B["t0"]) * q; z = min(z, f.camera(i, f._lb(i, t)).zoom)
        return d * z * self.g
