"""evren-anlamak topic palettes (engine Palette dicts). Brand caption colours constant in every palette."""
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
 # KOZMOS: deep-space ink; nebula = violet/magenta, stars = gold, 'dark matter' = teal-grey haze (the 95 % we can't see)
 "kozmos": P({
   "bg":     ["#04030A", "#0A0820", "#140F38", "#1F1752"],
   "body":   ["#1F1752", "#33246E", "#4E3592", "#7048AE", "#9C66C8", "#C99AE0", "#F3E6FA"],
   "dim":    ["#0A0820", "#141432", "#22284A", "#34405E", "#4E6A78"],
   "pale":   ["#4E6A78", "#7FA3B0", "#BFD6DC", "#EEF6F6"],
   "energy": ["#5A3A10", "#B8782A", "#FFC860", "#FFF1C8"],
   "accent": ["#3A0E3A", "#8A2A78", "#D84FA8", "#FF9AD0"]}, extra=["#2A8FB8", "#5FD6F0"]),
 # KARA TAHTA: green-black slate, chalk white, yellow + coral chalk, wooden frame (the 'rules' world)
 "kara_tahta": P({
   "bg":     ["#07110D", "#0C1A14", "#12261D", "#1A3428"],
   "body":   ["#1A3428", "#244536", "#305946", "#4A7560", "#7A9C88", "#B5C9B8", "#EEF2E6"],
   "dim":    ["#0C1A14", "#12261D", "#1A3428", "#244536", "#305946"],
   "pale":   ["#7A9C88", "#B5C9B8", "#DDE6D8", "#F6F8F0"],
   "energy": ["#12261D", "#B8962E", "#F2D06B", "#FFF0B8"],
   "accent": ["#3A2414", "#A8473A", "#F08A78", "#FFD0C4"],
   "board":  ["#0C1A14", "#12261D", "#1A3428"]}, extra=["#6A5418", "#5A1E18", "#5A3A22", "#8A5A32"]),
}
WHY = {
 "kozmos": "Space you can almost see: everything we observe (5 %) is gold/violet light; the 95 % (dark matter + dark energy) is a teal-grey haze ramp ('dim') that shimmers but never resolves.",
 "kara_tahta": "The rules: a classroom slate. Theory-of-everything / Hawking segments live on one chalkboard world, so 'the laws' have their own colour.",
 "hayret": "Brand Çini Gecesi returns only for the final 'hayret' moment: the channel's own colours = wonder.",
}
