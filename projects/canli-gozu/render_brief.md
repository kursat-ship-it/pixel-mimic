# Render brief: canli-gozu (for the render coder)

Spec: `spec.json`, built by `build_spec.py`; the vision definitions come from `visions.py`. Proxy: `spec_proxy.json` uses existing features and validates **OK** (one intended warning: 48.9 s > 45 s sweet spot).
The target errors in `retention_map.txt` are only "unknown scene vision_world / vision_mosaic".
Reference implementation of every vision mapping: **`vision_mock.py`** (numpy, ~200 lines). Port it; don't reinvent it.
`palette_board.png` = the mock output. `palette_board_engine.png` = proof that today's engine already accepts a palette *dict* in `spec.palette` (global, pure palette swap).

Timeline: 108 BPM, 4/4, 88 beats = 48.89 s, 30 fps, 1080×1920, grid 6 (art 180×320), pacing calm.

## 0. Why a palette swap is not enough
`palette_board_engine.png` shows the hero scene in all 7 palettes. It is a re-tint: no UV bullseye, no heat, no sonar.
A *vision mode* needs extra per-pixel material data. So the build is a **G-buffer + vision pass**, and the palette is only the last quantise step.

## 1. NEW: vision system (engine-wide, reusable)
**Spec**
- Top-level `visions`: `{mode: {palette:{colors,ramps,caption}, map, pixel?, blur?, label, receptors, why}}`. These are already written into spec.json from `visions.py`.
- Segment `vision: "<mode>"`. Fallbacks: `"hayret"` and any `PALETTES` name = plain palette (map `rgb`).
- Optional generic segment `palette: name|dict`, a per-segment palette override, also useful for other reels.
- Missing `vision` → `spec.palette` (today's behaviour). Nothing changes for old reels.

**Canvas aux planes** (art resolution, float32): `uv`, `temp`, `depth`, `oid` (int).
- Scenes that know about them write them with `cv.put_aux(mask, uv=, temp=, depth=, oid=)`.
- Every other draw (layers, props, particles, old scenes) writes defaults:
  - `uv = 0.3·lum`, `temp = 0.2`
  - `depth`: back layers 1.0, mid 0.5, front 0.3
  - `oid`: prop = unique id
- These defaults let props and layers show up as sonar edges and stay cold in thermal.

**Vision pass**, after the scene + layers + props and BEFORE narration/captions. Text is always composited in the brand caption colours, untouched.
Map formulas (exact code in `vision_mock.py: vision()`):

| map | formula |
|---|---|
| `rgb` | albedo |
| `bee_false_colour` | R = .82·G + .18·R (bee L), G = .95·B (bee M), B = uv (bee S) |
| `dichromat` | Machado 2009 deuteranopia matrix [[.367322,.860646,−.227968],[.280085,.672501,.047413],[−.011820,.042940,.968881]] in linear light (γ 2.2). Then `pixel: 2` = average 2×2 blocks + Bayer on the coarse grid (lower acuity) |
| `thermal` | gaussian(temp, σ = `blur` 2.0 art px) → palette ramp `body` (^0.9). Plus 18 % eye-image luminance × `pale`[.3] (the pit image is merged with vision in the tectum) |
| `sonar` | edges = Sobel(depth) > .08 ∪ oid boundaries, + 0.55 × iso-depth lines every 0.1. Echo = edges × (ring + 0.75·trail) + small fill; sky × .15. Ring: centre = the bat, radius R(t) grows from 0 at each **drum 'B' hit** at ≈ 300 art px / beat; ring = exp(−((d−R)/7)²), trail = exp(−(R−d)/70) for d < R. Up to 3 concurrent rings; older ones fade over `persistence_beats` 1.5. Ramp `body`, plus a faint 2-px wavefront in empty air |
| `bands12` | hue → 12 equal bands (+ a sine hue drift of .035 so gradients become stripes). Strong UV (uv > .85, not sky) = its own band at the violet end. S = 1, V in 3 steps |
| `coarse_classes` | hue → 5 flat classes (#E0503A #E8C838 #4FCB6A #3F6FD8 #B048D8); low saturation → #2E2456 family |

Then Bayer quantise to `visions[mode].palette.colors` (spread .11, screen-anchored, the same as `Palette.quantize`).

**Vision transitions.** When the outgoing and incoming segments use the same scene (`vision_world` → `vision_world`), keep ONE scene instance and continuous scene time across them. Bee flight, grass sway, water and the bat continue; nothing restarts.
- Render the frame twice (vision A, vision B) and let the transition's mask pick between them. The world doesn't cut, only the "eye" changes. iris = the hayret eye opens onto the new vision (S2); match / dissolve / crt / tiles / glitch behave as usual.
- S1 `params.peek {at:5, beats:.75, mode:"ari"}`: a 0.75-beat ordered-dither blink into the bee mode and back. This is the hook's curiosity flash; keep flash ≤ .35.
- S7 `params.collapse {from:"mantis12", beats:1}`: after the glitch, dither-dissolve mantis12 → mantis_kaba over 1 beat. The 12 bands visibly snap into 5 flat classes on the word "Ama".
- Ambient layers (stars, dust, bokeh, rays…) take their colours from the active mode's ramps automatically, through the per-mode Palette.

## 2. NEW scene `vision_world` (one coastal meadow, art 180×320, world origin = frame centre)
Layout = `vision_mock.py` (pixel coordinates there; world = (px−90, py−160)). Positions are fixed so the camera pans in the spec land on target:

| object | world centre | channels (uv / temp / depth) | animation |
|---|---|---|---|
| sky gradient + sun (56, −122) r 11 | top 150 px | .75 / .04 / 1 (sun 1/.25) | slow cloud drift (layer) |
| hills | y ≈ −30 | .12 / .25 / .85 | — |
| tree trunk (−75, −15), canopy (−66, −96) | left | .1 / .3 / .32 | canopy sway ±1 px / 2 beats |
| **bat** (−46, −52), hangs from branch | | .04 / **.92** / .28 | breathing; S5 wing-twitch on each 'B' click; S9 head turns to camera at beat 6 |
| **beehive** (63, 20) + label plate (63, 20) | right mid | wood .3 / **.62** (brood ≈ 35 °C) / .22 | bees in/out (2–3 px dots) |
| **flower** (2, 22): 8 petals r 9 + 15·cos^.6(4θ), disc r 5.5, stem to y 92 | centre | petals uv 0 **except r > 13 → .92 (bullseye)**, disc 0 / .4 / .11 | ±1 px sway |
| **bee** (22, 2), `bee_path`: approach (S1/S10, periodic so the loop matches) / land (S2) | | .15 / .55 / .10 | wing flicker each 16th |
| **red ball** (−48, 76) r 10 | lower left | .04 / .33 / .08 | still (S3 subject) |
| stone (36, 86); **mouse** (60, 78) | lower right | .25/.14 · .08/**1.0** | mouse sniff + tail flick (S4 subject) |
| sea y > 102, foam line, rocks | bottom strip | .3 / .18 / .18 | sine shimmer |
| **mantis shrimp** x −18…24, y ≈ 128 (6-colour segmented body, stalked eye at (24, 126) uv .9) | | .5–.9 / .2 / .14 | body wiggle, eye-stalk scan (Thoen: scanning eye movements) |

- `params.time`: day / dusk / night changes albedo lighting and the sky. Thermal and sonar ignore it.
- `focus()` returns the object named by `params.focus` (flower, ball, mouse, bat, shrimp, bat_hive). Callouts with `target:"focus"` and subject boxes rely on it. The spec also gives explicit `subject` world boxes.
- **POV hints (optional, nice):** S3 dog snout enters bottom-left for 1 beat; S4 snake head bottom-right with flicking tongue. Keep them inside the safe area and out of the bottom 18 %.
- Lower third is filled (meadow + sea), per the QC lesson. No empty first frames: every segment opens on the populated world.

## 3. NEW scene `vision_mosaic` (S8, the drop / cover frame at 37.5 s)
- 2×3 tiles in this order: insan, ari, kopek, yilan, yarasa, mantis12. Each tile = `vision_world` rendered through that mode, cropped around the flower (crop = world x −44…46, y −10…95 in mock px coords: cx0 46, cy0 150, 90×105).
- Tiles appear staggered every 0.25 beat on the drop. 1-art-px Kutu #04060E gutters.
- Sonar tile ring synced to 'B' hits; thermal tile shows the bee warm.
- No text in the tiles; the narration block on top carries the line.
- Proxy still: `assets/vis_mosaic.png`.

## 4. Tag (brand)
- S9: `plate` prop with `legible:true`, s 1.4. Render it as a **painted wooden label nailed on the beehive** (new `skin:"hive"` for plate when the scene is vision_world), text "@hayret.piksel", model line "KOVAN 07". It must stay readable at zoom 1.1–1.2 (≥ 5 px/dot) and clear of the NAGEL dialog box (proxy: plate at upper middle, dialog below).
- S5: the same label, `legible:false`. Draw it ONLY through the sonar pass: its letters are oid edges that light up when a ring passes. Subtle.
- Validator already counts 1 legible + 1 subtle; none in the first 2 s.

## 5. Music features to add (music.py)
1. **`pad.max_notes`** (default 4 = today). The mantis12 section has a 12-note chromatic cluster D3…C#4. Scale the per-note gain by 1/√n so the cluster is dense but not louder.
2. **Drum 'B' = bat chirp**: FM down-sweep 4 kHz → 1.5 kHz, 18 ms, slight noise, pan −.2. VOL ≈ .12, MIN_ENERGY 1.0.
   - **Multi-bar grids:** a drum string whose length is a multiple of the bar's steps = several bars (32 chars = 2 bars of 16ths).
   - The yarasa section uses `x...x...x.x.x.x.` then `x.x.x.x.rrrrrrrr` (`r` = existing 32nd ratchet) = the terminal buzz.
   - Expose 'B' hit beats to the scene so sonar rings start exactly on them (e.g. `film.drum_hits("B")`). Proxy maps B → R.
3. **Bug fix:** a 1-note chord in `progression` crashes the bass (`music.py:287`, `sorted(ch)[1]` IndexError). Guard it (third = root + 4 or root). The spec avoids it today with a D3+A3 dyad.
4. Everything else is existing features: per-section key/scale/progression as note lists, voices lists, fill, stop, riser, drop, logo at reveal+loop on voice `goz`, motif. The concept is in `music._concept`.
   - Per-section lead timbres: goz (human pulse), vizilti (bee), kuyruk (dog), isi (snake FM), sonar (bat ping + echo), prizma (mantis arp).
   - Pad note count = colour channels: 3 → 3 (shifted up) → 2 → 1 drone → none → 12 → octave.
5. Mix: keep `hf_shelf_db −3`, pulse bass at octave 3 (phone speakers). Proxy smoke test: −14 LUFS target, LRA 2.7, peak −4.3 dBFS.

## 6. Narration (already standard, §12.6)
- All blocks: word reveal at 16th (callout 8th). Placements: top, callout (S2 → flower (2, 22), side right), auto (S4), panel (S5), mid head (S7), top head (S8), dialog "NAGEL, 1974" (S9).
- The validator passes reading time on the proxy. When the real scene exists, re-run `validate spec.json` for the narration layout and subject-overlap checks.

## 7. Camera (calm)
Every segment has a slow `inOutSine` zoom (≤ 0.06 ln/s) and a small pan. Pan targets are in world coords (camera centre):

| seg | camera centre (target) |
|---|---|
| S1/S2 | flower (2, 18 → 22) |
| S3 | ball (−44, 64 → −48, 70) |
| S4 | mouse (56, 68 → 58, 74) |
| S5 | (−8, −16 → −10, −22): bat + label in view |
| S6/S7 | shrimp (2, 112 → 0, 118) |
| S9 | (−20, −30 → −22, −36) |
| S10 | ends on exactly S1 frame 0: zoom 1.25, pan (0, 6), bee at `approach` t = 0 |

## 8. Acceptance checks
- `bitloop validate spec.json`: 0 errors, only the duration warning.
- The bullseye is visible in S2 (magenta tips vs dark-red base). In S3 the ball and the grass are within ΔE < 10 of each other (dog). In S4 the mouse is the brightest object. In S5 rings start within 1 frame of each 'B' hit. In S7 the colour count visibly drops (12 → 5).
- Loop: last frame == frame 0 (S10 → S1), and the sonic logo is on the seam.
- Text never in the bottom 18 % / right 12.5 %. Flash ≤ .35, shake calm.
- Cover = 37.5 s (mosaic + "Altı göz, tek dünya…").
