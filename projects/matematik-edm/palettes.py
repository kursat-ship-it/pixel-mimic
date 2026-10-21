"""matematik-edm topic palette (engine Palette dict): black + neon magenta. Brand caption colours constant."""
BRAND_CAPTION = {"box": "#04060E", "text": "#F4ECDC", "hi": "#41E8D2", "hi2": "#FF9A86"}


def P(ramps, extra=()):
    cols = []
    for r in list(ramps.values()) + [list(extra)]:
        for c in r:
            if c not in cols: cols.append(c)
    for c in ("#04060E", "#F4ECDC", "#41E8D2", "#FF9A86"):
        if c not in cols: cols.append(c)
    return {"colors": cols, "ramps": ramps, "caption": dict(BRAND_CAPTION)}


PALETTES = {
    # NEON: near-black digital lab, neon magenta = the signal, white-magenta = the tracking dot / text,
    # electric cyan used only as a rare second accent (axis ticks / drop particles).
    "neon": P({
        "bg":     ["#0A0A0A", "#120812", "#1A0C1A", "#241024"],
        "body":   ["#2A0A2A", "#5A0E5A", "#A010A0", "#D014D0", "#F020F0", "#FF80FF", "#FFD0FF"],
        "dim":    ["#1A0C1A", "#2A1030", "#3A1440", "#4A1848"],
        "pale":   ["#6A206A", "#A030A0", "#D060D0", "#F0A0F0", "#FFF0FF"],
        "energy": ["#5A005A", "#A000A0", "#E000E0", "#FF00FF", "#FFA0FF"],
        "accent": ["#0A3A3A", "#0A8080", "#00E0E0", "#A0FFFF"]}, extra=["#FF40A0", "#00FFFF"]),
}
WHY = {"neon": "Black + neon magenta: an underground techno / digital math lab. The signal is magenta, the tracking "
               "dot is black, cyan is a rare digital accent. Brand caption colours stay Çini Gecesi."}
