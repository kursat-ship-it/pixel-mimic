"""Locked palettes + ordered (Bayer 4x4) quantisation to the palette."""
import numpy as np

def _hex(h):
    h = h.lstrip('#'); return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]

# Reference-locked palette (from LXcZhstWlXM): dark violet world, amber = energy.
# @hayret.piksel identity — "Çini Gecesi" (İznik tile night): cobalt night, turquoise wonder, coral heat, cream light.
HAYRET_NAMES = {
    "#060814": "Gece", "#0B1230": "Derin Lacivert", "#141E4A": "Mürekkep", "#1E2E73": "Kobalt Koyu",
    "#2C47A6": "Kobalt", "#4169D1": "Lapis", "#77A2EE": "Gök", "#B8CDF2": "Sis", "#F4ECDC": "Krem",
    "#0B4F5C": "Derin Firuze", "#13A39B": "Firuze", "#41E8D2": "Türkuaz Işık", "#D2FFF5": "Parıltı",
    "#7E1F35": "Kiremit", "#EC4A57": "Çini Mercanı", "#FF9A86": "Mercan Işık", "#04060E": "Kutu",
}
PALETTES = {
    "hayret": {
        "colors": list(HAYRET_NAMES),
        "ramps": {
            "bg": ["#060814", "#0B1230", "#141E4A", "#1E2E73"],
            "body": ["#141E4A", "#1E2E73", "#2C47A6", "#4169D1", "#77A2EE", "#B8CDF2", "#F4ECDC"],
            "dim": ["#0B1230", "#141E4A", "#1E2E73", "#2C47A6", "#4169D1"],
            "pale": ["#1E2E73", "#2C47A6", "#77A2EE", "#B8CDF2", "#F4ECDC"],
            "energy": ["#0B4F5C", "#13A39B", "#41E8D2", "#D2FFF5"],
            "accent": ["#7E1F35", "#EC4A57", "#FF9A86", "#F4ECDC"],
        },
        "caption": {"box": "#04060E", "text": "#F4ECDC", "hi": "#41E8D2", "hi2": "#FF9A86"},
    },
    "violet-amber": {
        "colors": ["#07030C", "#11071A", "#1A0C26", "#221031", "#2C1436", "#3D2265", "#4F2C61",
                   "#5B3789", "#6E3FAC", "#8854B6", "#B087DC", "#D6BAE6", "#F4ECEB",
                   "#5A2418", "#AB603A", "#E5AF4D", "#F8D070", "#FFF4D2"],
        # named ramps, dark -> light (used by scenes for shading)
        "ramps": {
            "bg": ["#07030C", "#11071A", "#1A0C26", "#221031"],
            "body": ["#221031", "#3D2265", "#5B3789", "#6E3FAC", "#8854B6", "#B087DC", "#D6BAE6", "#F4ECEB"],
            "dim": ["#11071A", "#2C1436", "#4F2C61", "#8854B6", "#B087DC"],
            "pale": ["#2C1436", "#4F2C61", "#8854B6", "#B087DC", "#D6BAE6", "#F4ECEB"],
            "energy": ["#5A2418", "#AB603A", "#E5AF4D", "#F8D070", "#FFF4D2"],
        },
        "caption": {"box": "#05000C", "text": "#F0E8F0", "hi": "#F8D070", "hi2": "#AB603A"},
    },
    # variants keep the same structure so any scene works with any palette
    "teal-coral": {
        "colors": ["#02080A", "#061418", "#0A1E24", "#102A30", "#16363C", "#1E4A52", "#28606A",
                   "#2F7A84", "#3A96A0", "#57B4BA", "#8AD2D2", "#C2EAE6", "#F0FAF6",
                   "#4A1A16", "#B4503C", "#F07A5A", "#FFB08A", "#FFE8D8"],
        "ramps": {
            "bg": ["#02080A", "#061418", "#0A1E24", "#102A30"],
            "body": ["#102A30", "#1E4A52", "#28606A", "#2F7A84", "#3A96A0", "#57B4BA", "#8AD2D2", "#F0FAF6"],
            "dim": ["#061418", "#16363C", "#1E4A52", "#3A96A0", "#57B4BA"],
            "pale": ["#16363C", "#28606A", "#3A96A0", "#57B4BA", "#C2EAE6", "#F0FAF6"],
            "energy": ["#4A1A16", "#B4503C", "#F07A5A", "#FFB08A", "#FFE8D8"],
        },
        "caption": {"box": "#00060A", "text": "#EAF6F4", "hi": "#FFB08A", "hi2": "#F07A5A"},
    },
}

BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16.0


class Palette:
    def __init__(self, name_or_spec="hayret"):
        spec = PALETTES[name_or_spec] if isinstance(name_or_spec, str) else name_or_spec
        self.name = name_or_spec if isinstance(name_or_spec, str) else "custom"
        self.colors = np.array([_hex(c) for c in spec["colors"]], np.float32)
        self.ramps = {k: np.array([_hex(c) for c in v], np.float32) for k, v in spec["ramps"].items()}
        self.ramps.setdefault("accent", self.ramps["energy"])
        self.caption = {k: tuple(int(round(x * 255)) for x in _hex(v)) for k, v in spec["caption"].items()}
        self.bg = self.ramps["bg"]

    def ramp(self, name, t):
        """Continuous colour along a ramp, t in [0,1] (array ok) -> (..., 3)."""
        r = self.ramps[name]; t = np.clip(np.asarray(t, np.float32), 0, 1) * (len(r) - 1)
        i = np.minimum(t.astype(int), len(r) - 2); f = (t - i)[..., None]
        return r[i] * (1 - f) + r[i + 1] * f

    def quantize(self, rgb, spread=0.11, phase=(0, 0)):
        """Ordered-dither rgb (H,W,3 float 0..1) to palette indices -> uint8 RGB.
        The Bayer pattern is anchored to the screen (art pixels) so flat areas never swim."""
        H, W, _ = rgb.shape
        by = np.tile(BAYER4, (H // 4 + 1, W // 4 + 1))[:H, :W]
        x = rgb + (by[..., None] - 0.5) * spread
        d = ((x[:, :, None, :] - self.colors[None, None]) ** 2).sum(-1)
        idx = d.argmin(-1)
        return (self.colors[idx] * 255 + 0.5).astype(np.uint8)


def _lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def contrast(a, b):
    """WCAG 2 contrast ratio between two #RRGGBB colours."""
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + .05) / (lb + .05)
