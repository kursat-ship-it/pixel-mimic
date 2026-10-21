"""canli-gozu: per-creature VISION MODES = palette (engine Palette dict: colors+ramps+caption) + channel mapping.
Single source of truth for build_spec.py (spec "visions" block), vision_mock.py (palette_board / proxy stills)
and the render coder. Caption colours stay brand (Çini Gecesi) in every mode: the brand layer never changes."""

BRAND_CAPTION = {"box": "#04060E", "text": "#F4ECDC", "hi": "#41E8D2", "hi2": "#FF9A86"}

def P(ramps, extra=()):
    cols = []
    for r in list(ramps.values()) + [list(extra)]:
        for c in r:
            if c not in cols: cols.append(c)
    for c in ("#04060E", "#F4ECDC"):               # caption box/text must exist in every mode
        if c not in cols: cols.append(c)
    return {"colors": cols, "ramps": ramps, "caption": dict(BRAND_CAPTION)}

VISIONS = {
 # ---- 1. İNSAN: trichromat baseline (S/M/L cones ≈ 420/530/560 nm). Natural daylight meadow, the "reference".
 "insan": {"label": "İNSAN · 3 koni", "receptors": 3, "map": "rgb",
   "why": "Baseline trichromat. Daylight meadow in natural hues; the yellow flower is plain yellow (no pattern), the red ball pops on green grass.",
   "palette": P({
     "bg":     ["#0E1B2E", "#1C3550", "#2F5F86", "#5E9CC8"],
     "body":   ["#1A2414", "#2E4A22", "#3F7A2E", "#63A83A", "#9FD05A", "#D9EFA0", "#FFF8E6"],
     "dim":    ["#1A2230", "#2B3A4A", "#46596B", "#6F8494", "#A3B3BE"],
     "pale":   ["#5E9CC8", "#8EC3E6", "#BFE3F5", "#E8F6FC"],
     "energy": ["#7A4A00", "#D18A00", "#FFC21A", "#FFE680"],
     "accent": ["#5E0F14", "#B3202A", "#E8403A", "#FF8C7A"]},
     extra=["#4A2E1A", "#8A5A32", "#C49060", "#7A6A5A"])},
 # ---- 2. ARI: UV/blue/green trichromat (peaks 344/436/544–556 nm). FALSE COLOUR, the standard convention of UV
 #      photography for bees: display R←bee green(L), G←bee blue(M), B←bee UV(S). Foliage turns rust/red, sky mint,
 #      UV-reflecting petal tips magenta, UV-absorbing petal base dark red → the hidden BULLSEYE appears.
 "ari": {"label": "ARI · morötesi", "receptors": 3, "map": "bee_false_colour",
   "why": "UV becomes visible as magenta; bee's 'green' shown as red. Red objects lose contrast (bees see red only weakly through the L receptor).",
   "palette": P({
     "bg":     ["#0E2A2A", "#1E5A52", "#4FA88E", "#A8E8C8"],
     "body":   ["#1A0606", "#3E100C", "#6E2014", "#9E3A1C", "#C8602A", "#E8904A", "#FFD0A0"],
     "dim":    ["#120A14", "#2A1428", "#462240", "#6A345A", "#8E4A70"],
     "pale":   ["#A8E8C8", "#D0F8E8", "#F4FFF8"],
     "energy": ["#4A0A4A", "#8E1A90", "#D040D8", "#FF90F8"],
     "accent": ["#2A0606", "#5A0E0E", "#8A1E1E", "#C04040"]})},
 # ---- 3. KÖPEK: dichromat (cones ≈ 429 & 555 nm, Neitz 1989) ≈ human deuteranope → only a BLUE↔YELLOW axis,
 #      red/orange/green collapse to olive-yellow-grey; acuity ≈ 20/75 → rendered at HALF resolution (2×2 art px).
 "kopek": {"label": "KÖPEK · 2 koni", "receptors": 2, "map": "dichromat", "pixel": 2,
   "why": "Blue-yellow only (Machado 2009 deuteranopia matrix). The red ball and the green grass become the same dull olive. Coarser pixels = lower acuity.",
   "palette": P({
     "bg":     ["#0D1626", "#1C2E4D", "#34507D", "#5878A8"],
     "body":   ["#1C1A12", "#3A3522", "#5E573A", "#8A8154", "#B5AA72", "#DCD29A", "#F6F0D2"],
     "dim":    ["#15161A", "#2A2C30", "#45484C", "#6C6E6E", "#9A9A94"],
     "pale":   ["#5878A8", "#8AA4C8", "#BCCBE0", "#E6ECF2"],
     "energy": ["#4A4220", "#8C7C36", "#C9B451", "#F0DE80"],
     "accent": ["#2E2A1C", "#575034", "#807650", "#A89C70"]})},
 # ---- 4. ÇINGIRAKLI YILAN: pit organ (TRPA1 heat sensing, Gracheva 2010) = blurry pinhole THERMAL map, merged in
 #      the optic tectum with the normal eye image (Newman & Hartline 1981). Thermal ramp + faint eye-image edges.
 "yilan": {"label": "YILAN · ısı", "receptors": "IR çukur", "map": "thermal", "blur": 2.0,
   "why": "Cold = indigo, warm = yellow-white. Warm mouse, warm beehive, bat glow; stone and water vanish. Slight blur = pinhole optics.",
   "palette": P({
     "bg":     ["#04020A", "#0E0624", "#1C0A44", "#2E0E5E"],
     "body":   ["#1C0A44", "#3E1070", "#6E1A7E", "#A8286E", "#D84A4A", "#F2803A", "#FFC24A"],
     "dim":    ["#0A0418", "#160A30", "#24104A", "#341660", "#4A1E74"],
     "pale":   ["#A8286E", "#F2803A", "#FFC24A", "#FFF0A0"],
     "energy": ["#F2803A", "#FFC24A", "#FFF0A0", "#FFFFF4"],
     "accent": ["#6E1A7E", "#D84A4A", "#FF9A5A", "#FFE8C0"]})},
 # ---- 5. YARASA: echolocation, an AUDITORY scene. Visualised as a monochrome sonar contour map that exists only
 #      where echoes return: each call = expanding ring; edges light up when the ring passes, then fade (persistence).
 "yarasa": {"label": "YARASA · yankı", "receptors": "ses", "map": "sonar",
   "why": "Firuze-mono (brand turquoise family) so 'sound' reads as a different sense, not a colour. Sky = no echo = black.",
   "palette": P({
     "bg":     ["#000505", "#021612", "#053026", "#0A4C3A"],
     "body":   ["#053026", "#0A4C3A", "#127456", "#22A07A", "#4CD6A8", "#A6FFE0", "#F0FFF8"],
     "dim":    ["#021612", "#053026", "#0A4C3A", "#127456", "#22A07A"],
     "pale":   ["#22A07A", "#4CD6A8", "#A6FFE0", "#F0FFF8"],
     "energy": ["#4CD6A8", "#A6FFE0", "#F0FFF8", "#FFFFFF"],
     "accent": ["#127456", "#4CD6A8", "#A6FFE0", "#F0FFF8"]})},
 # ---- 6a. MANTİS KARİDESİ (hype): 12 colour receptor types 300–720 nm → 12 hue BANDS incl. 'UV' as its own band.
 "mantis12": {"label": "MANTİS · 12 alıcı", "receptors": 12, "map": "bands12",
   "why": "What everyone imagines: hyper-saturated 12-band rainbow. Shown first, then corrected.",
   "palette": P({
     "bg":     ["#07030F", "#1A0E2E", "#2A1650", "#3C1F70"],
     "body":   ["#1F5BFF", "#1FB4FF", "#1FFFD8", "#1FFF6A", "#7CFF1F", "#E8FF1F", "#FFB81F"],
     "dim":    ["#07030F", "#1A0E2E", "#2A1650", "#3C1F70", "#6A1FFF"],
     "pale":   ["#C81FFF", "#FF1FC8", "#FF1F4B", "#FF6A1F", "#FFFFFF"],
     "energy": ["#6A1FFF", "#C81FFF", "#FF1FC8", "#F6E8FF"],
     "accent": ["#FF1F4B", "#FF6A1F", "#FFB81F", "#FFF0C8"]})},
 # ---- 6b. MANTİS (Thoen 2014): poor discrimination (Δλ 12–25 nm vs 1–4 nm in humans) → colours RECOGNISED in
 #      a few broad classes, not finely told apart. Same scene collapses to ~5 flat classes.
 "mantis_kaba": {"label": "MANTİS · gerçekte?", "receptors": 12, "map": "coarse_classes",
   "why": "Twist: 12 channels but coarse colour judgement. Hues snap to 5 broad flat classes; fine gradients disappear.",
   "palette": P({
     "bg":     ["#07030F", "#1E1438", "#2E2456"],
     "body":   ["#2E2456", "#3F6FD8", "#4FCB6A", "#E8C838", "#E0503A"],
     "dim":    ["#07030F", "#1E1438", "#2E2456"],
     "pale":   ["#3F6FD8", "#4FCB6A", "#E8C838", "#F4ECDC"],
     "energy": ["#2E2456", "#B048D8", "#E8C838", "#F4ECDC"],
     "accent": ["#2E2456", "#E0503A", "#E8C838", "#F4ECDC"]})},
}
# brand night palette (Nagel / loop frame at dusk) = the channel's own "Çini Gecesi" = 'hayret' in the engine.
ORDER = ["insan", "ari", "kopek", "yilan", "yarasa", "mantis12", "mantis_kaba"]

def union_palette(base_ramps_from="insan"):
    """PROXY ONLY: one engine palette that contains every vision colour so `image` stills keep their vision hues
    (the engine has one global palette today). Ramps come from one mode, so ambient layers look 'human'."""
    cols = []
    for k in ORDER:
        for c in VISIONS[k]["palette"]["colors"]:
            if c not in cols: cols.append(c)
    import copy
    p = copy.deepcopy(VISIONS[base_ramps_from]["palette"]); p["colors"] = cols
    return p
