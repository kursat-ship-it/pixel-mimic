"""The stargazer kid ("Meraklı"): a small child in a bobble hat and a türkuaz sweater, sitting on a hill.
Same char-map sprite format as sprites.py (bottom row = seat line, anchor bottom-centre), 20×24 cells.
Roles are hex colours snapped to the active palette at draw time (sprites.draw_sprite(..., roles=KID_ROLES, snap=True)),
so the kid stays flat-coloured and readable in Kozmos, Kara Tahta and the brand palette alike.

frames  up      profile facing right, head tilted back, looking at the sky (hook frame 0)
        up_blink
        q       three-quarter, turning toward the camera
        front   facing the camera, small smile          front_blink   wow (eyes wide, little 'o' mouth)"""
from .sprites import draw_sprite

KID_ROLES = {
    "o": "#04030A",  # outline
    "H": "#D84FA8",  # bobble hat
    "I": "#8A2A78",  # hat brim / shade
    "P": "#F4ECDC",  # pompom
    "h": "#5A3A10",  # hair
    "j": "#B8782A",  # hair highlight
    "f": "#FFF1C8",  # skin
    "g": "#FFC860",  # skin shade
    "b": "#FF9A86",  # blush
    "e": "#04030A",  # eyes
    "w": "#EEF6F6",  # eye sparkle
    "m": "#8A2A78",  # mouth
    "s": "#41E8D2",  # sweater
    "t": "#2A8FB8",  # sweater shade
    "S": "#F4ECDC",  # sweater stripe
    "p": "#33246E",  # trousers
    "q": "#1F1752",  # trousers shade
    "k": "#FFC860",  # boots
    "K": "#B8782A",  # boot shade
}

KID = {
 "front": [
  "........oooo........",
  ".......oPPPPo.......",
  ".......oPPPPo.......",
  "......ooHHHHoo......",
  ".....oHHHHHHHHo.....",
  "....oHHHHHHHHHHo....",
  "...oHHHHHHHHHHHHo...",
  "...oIIIIIIIIIIIIo...",
  "..ohhjffffffffjhho..",
  "..ohffffffffffffho..",
  "..offeeffffffeeffo..",
  "..offewffffffewffo..",
  "..ofbbffffffffbbfo..",
  "...offfffmmfffffo...",
  "....offffffffffo....",
  ".....oooggggooo.....",
  "....ostsSSSSstso....",
  "...ossssssssssssto..",
  "..otsSSSSSSSSSSssto.",
  "..offsssssssssssffo.",
  ".oqpppppppppppppppo.",
  "okkpppqqqqqqqqpppkko",
  "okKkoooooooooooKkkKo",
  ".oooo..........oooo.",
 ],
 "up": [
  "....................",
  "....................",
  ".......oooo.........",
  "......oPPPPo........",
  "......oPPPPo........",
  "....ooooHHHooo......",
  "...oHHHHHHHHHHo.....",
  "..oHHHHHHHHHHHHo....",
  "..oHHHHHHHHHHIIIo...",
  "..ohhhhhhhhIIffffo..",
  "..ohhhhhhhhfffewffo.",
  "..ohhhhjhhfffffffffo",
  "...ohhhhhhffffbbffo.",
  "....ohhhhffffffmfo..",
  ".....oooooffffffo...",
  "......otssssooo.....",
  ".....ossSSSSso......",
  "....osssssssoooo....",
  "....osSSSSSsffppo...",
  "...ossssssspppppko..",
  "...otsssssppppqqkko.",
  "..otppppppppqqqpKkko",
  "..oqqqqqqqqqqqqqoooo",
  "...oooooooooooooo...",
 ],
 "q": [
  "........oooo........",
  ".......oPPPPo.......",
  ".......oPPPPo.......",
  ".....oooHHHHoo......",
  "....oHHHHHHHHHo.....",
  "...oHHHHHHHHHHHo....",
  "..oHHHHHHHHHHHHHo...",
  "..oIIIIIIIIIIIIIo...",
  "..ohhhjffffffffho...",
  "..ohhffffffffffffo..",
  "..ohfffeeffffeefo...",
  "..ohfffewffffewfo...",
  "..ohffbbfffffbbfo...",
  "...ohffffffmmffo....",
  "....offffffffffo....",
  ".....oooggggooo.....",
  "....ostsSSSSstso....",
  "...ossssssssssssto..",
  "..otsSSSSSSSSSSssto.",
  "..offsssssssssssffo.",
  ".oqpppppppppppppppo.",
  "okkpppqqqqqqqqpppkko",
  "okKkoooooooooooKkkKo",
  ".oooo..........oooo.",
 ],
}


def _with(rows, edits):
    g = [list(r) for r in rows]
    for r, c, ch in edits: g[r][c] = ch
    return ["".join(r) for r in g]


F = KID["front"]
KID["front_blink"] = _with(F, [(10, 5, "f"), (10, 6, "f"), (10, 13, "f"), (10, 14, "f"), (11, 5, "e"), (11, 6, "e"),
                               (11, 13, "e"), (11, 14, "e")])
KID["wow"] = _with(F, [(9, 5, "e"), (9, 6, "e"), (9, 13, "e"), (9, 14, "e"), (13, 9, "o"), (13, 10, "o"),
                       (14, 9, "m"), (14, 10, "m")])
KID["up_blink"] = _with(KID["up"], [(10, 14, "f"), (10, 15, "f"), (11, 14, "g"), (11, 15, "g")])


def _check():
    for k, f in KID.items():
        assert len(f) == 24 and all(len(r) == 20 for r in f), (k, len(f), [len(r) for r in f])
        assert set("".join(f)) <= set(KID_ROLES) | {"."}, (k, set("".join(f)) - set(KID_ROLES))


_check()
SEAT = 2          # rows below the seat line (boots) — the sprite's bottom sits this many cells under the hip


def draw_kid(cv, frame, x, y, scale=2.0, alpha=1.0, flip=False):
    """(x, y) = bottom-centre of the sprite in world units; scale = world units per sprite cell."""
    draw_sprite(cv, KID[frame], x, y, scale, flip=flip, alpha=alpha, roles=KID_ROLES, snap=True)
