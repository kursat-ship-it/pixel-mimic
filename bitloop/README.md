# bitloop v2: the @hayret.piksel reel engine

bitloop turns a **spec (JSON)** into a finished vertical pixel-art reel (1080×1920, 30 fps, H.264 + AAC, −14 LUFS).
It runs on pure Python + numpy + ffmpeg with no samples or API keys. A spec has three parts:

- **Brand layer (constant, preset `hayret`).**
  - Çini Gecesi palette and the hayret eye mark.
  - Diegetic `@hayret.piksel` tag rules.
  - Pixel font (full Turkish), narration text system + short captions, 30 fps, at least 3 moving layers per scene.
  - **Pacing preset** `"pacing": "calm"` (default since Oct 2026) or `"punchy"` (the first two reels).
  - The **4-note sonic logo motif** (5→1→2→3, short-short-short-LONG). It is transposed and re-harmonised into each video's own key, scale and lead timbre.
- **Music design (per video).** Any tempo, meter, key, scale or makam, plus voices, drums, motif and sections, with tempo/meter/key changes.
- **Edit / structure (per video).** A free list of segments: any count and length, scene, layers, props, camera, transition, narration blocks, captions and events.

There is **no fixed template**. Archetypes are optional starting points.
**Authoring guide + retention playbook (Turkish):** `../recipe/recipe.md` §12 (narration §12.6, pacing §12.7). **Planner/researcher guide:** `../recipe/RESEARCHER_GUIDE.md`. **Full schema:** `../recipe/recipe.json` → `spec_schema`.

## Quick start
```bash
cd bitloop                                         # from the repo root
./bitloop.sh list archetypes                       # also: styles scales drums transitions props scenes
./bitloop.sh init ../projects/my-topic --archetype cosmic_zoom_out    # or blank / reference / …
#   design the music + edit for the topic, fill every {{slot}}
./bitloop.sh validate ../projects/my-topic/spec.json   # brand/quality rules + RETENTION MAP (review before rendering)
./bitloop.sh music  ../projects/my-topic/spec.json -o ../projects/my-topic/music.wav   # listen first
./bitloop.sh sheet  ../projects/my-topic/spec.json -o ../projects/my-topic/sheet.jpg
./bitloop.sh render ../projects/my-topic/spec.json -o ../projects/my-topic/draft.mp4 --draft   # 15 fps preview
./bitloop.sh render ../projects/my-topic/spec.json -o ../projects/my-topic/reel.mp4 --package  # final 30 fps + cover + upload.json
```
Tests (from `bitloop/`, repo venv active): `python -m pytest tests -q` or one file at a time, e.g. `python tests/test_narration.py` (10 tests: measured legibility floor, Turkish wrap/hyphenation, typewriter on the 16th grid + blips in the event timeline and audio, layout safe zones/subject avoidance, palette-safe frames, wipe exit, loop seam, reading-time + calm-pacing rules), `tests/test_engine.py` (14 tests), `tests/test_fractal.py` (12 tests: series self-similarity, Shepard riser, new scenes, vinyl, loop seam, spin-over, snapped text, portal) and `tests/test_story.py` (10 tests: series_defs, lookahead, section gain, hero sprites, story scenes populated at frame 0 + lower third + on palette, determinism, Libet/dice/domino mechanics, book legibility, loop seam).

## One clock
- The timeline unit is **1 beat = 1 quarter note**, always. `bpm` is quarter notes per minute.
  A 7/8 bar is 3.5 beats, a 6/8 bar 3 beats, a 9/8 bar 4.5 beats.
- Segments and sections take `beats` or `bars`. Bars use the meter in force at that point.
- Music sections define the **tempo map**: `bpm`, plus `bpm_to` for a linear accelerando or ritardando.
  `timing.TempoMap` integrates it (trapezoid rule) to convert beats ↔ seconds.
- Frames, notes, drums, SFX, captions, transitions, shake and flash all go through this one map.
- Measured:
  - Video cuts land within 2 ms of the tempo-mapped time.
  - Downbeats stay within 5 ms through 90→150 BPM accel + 7/8 + 3/4 ritardando (unit test).
- `spec.timeline_events()` is the single event list feeding SFX (music.py), shake/flash/punch (render.py) and the retention map.

## Spec at a glance
```jsonc
{
  "version": 2, "preset": "hayret",
  "meta": { "title": "…🎧", "description": "…", "hashtags": ["#…"], "lang": "tr" },
  "music": {
    "style": "aksak_phrygian",           // optional starting point (bitloop list styles); every key below overrides it
    "bpm": 140, "meter": "7/8", "grouping": [2,2,3], "key": "E", "scale": "phrygian", "tuning": "12tet",  // or "approx" (makam microtones)
    "flavour": "sid",                    // 2a03 | gameboy | sid | fm  (default timbres for each role)
    "progression": ["I","II","I","VII"], // roman (plain = diatonic to the scale; bVI / V7 / viio force quality) | "Em" "C#m7" | ["E3","G3","B3"]
    "chord_bars": 1, "swing": 0, "seed": 3,
    "voices": {                          // roles: lead counter arp bass pad; any names, any number
      "lead": { "type": "pulse", "duty": 0.25, "vibrato": 0.15, "sweep": 0, "arp": null, "glide": 0, "octave": 5, "echo": 0.75 },
      "arp":  { "pattern": "groups", "rate": 2 },            // up down updown broken alberti pedal groups oompah
      "bass": { "pattern": "groups" },                       // chip root8 octave walk pump groups waltz sustain | [semitones|null]
      "pad":  { "type": "wave", "table": "organ", "min_energy": 1.5 },
      "slow": { "series": { "name": "norgard", "rate": 1, "sign": 1 } } },  // integer-series melody on the global grid (see below)
    "drums": "aksak_7_8",                // four_on_floor breakbeat trap half_time boom_bap maqsum aksak_9_8 aksak_7_8 waltz six_eight shuffle march dnb auto none | {"K":"X...","S":"....X..."}
    "motif": { "contour": "zigzag", "range": 6, "density": 0.6, "seed": 5 },   // or {"notes":[0,2,4,null], "rhythm":[0.5]}
    "sections": [                        // any number; omit → one per segment (build=riser, hit/drop=drop, hold=stop)
      { "name": "a", "bars": 4, "energy": 1.5 },
      { "name": "b", "bars": 2, "energy": 2.5, "fill": true, "riser": true, "riser_kind": "shepard", "stop": 0.5 },
      { "name": "c", "bars": 4, "energy": 3, "drop": true, "key": "F#", "scale": "lydian", "bpm_to": 150, "voices_in": ["counter"] } ],
    "logo": { "at": ["reveal", "loop"] },
    "sfx": { "hit": "boom", "tick": null } },   // remap / mute any event kind
  "loop": true, "loop_transition": { "type": "mosaic", "beats": 1 },
  "segments": [
    { "id": "S1", "role": "hook", "scene": "hero", "beats": 7, "params": {},
      "layers": { "back": ["horizon","nebula","stars"], "front": ["bokeh","dust"] },
      "props": [ { "kind": "neon_sign", "x": 0, "y": -110, "s": 1, "layer": "back", "par": 0.4 } ],
      "camera": { "zoom": [1.0, 1.25], "pan": [[0,0],[0,10]], "rot": [0,0], "orbit": 3, "ease": "inOutSine" },
      "transition_in": "cut",            // or { "type": "whip", "beats": 0.5, "dir": "left" } …
      "narration": [ { "text": "Bir sinyal beyninde *ne kadar hızlı* gider?", "at": 0, "place": "top", "size": "head", "reveal": "word", "rate": "8th" } ],
      "caption": { "text": "BU NE KADAR\n*HIZLI?*", "at": [0, 5] },   // optional short ALL-CAPS caption (legacy top box)
      "events": [ { "at": 3.5, "kind": "punch" }, { "at": 5, "kind": "rehook", "label": "yeni soru" } ] } ]
}
```
- **Series voices** (`voices.X.series`): `{"name":"norgard","rate":4,"div":1,"sign":1|-1,"invert":false,"offset":0,"gate":.92,"phase":"global"|"section","logo_duck":.3}`.
  Note i = floor(beat·rate/div) on the GLOBAL beat grid → scale degree sign·a(i)+offset in the section's scale/key (diatonic; a scale change at a drop re-colours the same series).
  Nørgård's infinity series a(2n)=−a(n), a(2n+1)=a(n)+1: a voice at rate 1 plays exactly every 4th note of a rate-4 voice, a rate-2 voice with sign −1 every 2nd (unit-tested).
  Series voices skip chords/motif; inside sonic-logo windows lead/counter series voices duck to `logo_duck` (they keep playing so on-screen lit notes stay in sync).
- **Custom series** (`music.series_defs`): `{"kehanet": {"values": [0,2,4,2,…], "period": 16}}` (or a bare list) registers a finite melody as a periodic integer series, usable by voices (`series.name`) and scenes (`future_book.roll_series`, `actual_series`). Re-loading a spec drops the previous spec's list series. **`series.lookahead: k`**: slot n plays value n+k (a "whisper" voice one note in the future). **`sections[].gain`** `{voice: k}` trims one voice in one section.
- **Shepard riser** (`sections[].riser_kind:"shepard"`, with `riser:true`): 7 octave-spaced chip partials stepping a semitone per 16th under a Gaussian loudness curve, crescendo, `shepard_hops` blips per beat; ends where `stop` begins.
- **Layer kwargs:** any layer may be `{"kind":"nebula","ramps":["dim","energy","body"]}` / `{"kind":"bokeh","ramps":["pale","energy"]}` (drop the coral light behind pale line-art).
- **`layer_sync: "first"`** on the loop segment: reuses segment 1's layer stack on the loop clock so the last frame matches frame 0.
- **Props:** `chalkboard` and `terminal` take `lines:[...]` (formula / boot text); the terminal widens to fit. Plate and terminal text is snapped (pixel-exact under zoom); the plate mattes its glow. `Canvas.matte(x,y,w,h,k)` clears additive glow under any in-world label.
- **Roles** (free vocabulary; they feed the retention checks and default music behaviour):
  hook promise step build hold drop hit rehook number twist reveal payoff metaphor system contrast loop free.
- **Events** `punch shake flash pulse pop rehook twist reveal mark` sit on beats. Each fires its SFX, unless you set `sfx` to null or remap it.

### Libraries
| | |
|---|---|
| **Scales (23)** | major minor dorian phrygian lydian mixolydian locrian harmonic_minor melodic_minor phrygian_dominant pentatonic_major pentatonic_minor blues whole_tone chromatic hirajoshi · makams **hicaz uşşak kürdi nihavend rast hüzzam saba**. Makams are 12-TET by default; `tuning: "approx"` gives approximate microtones |
| **Meters** | any n/d; default aksak groupings 5/8 7/8 9/8 10/8 11/8 (override with `grouping`) |
| **Voices** | pulse (duty, PWM, detune), triangle (4-bit stepped), saw, wave (Game Boy 32×4-bit tables), fm (2-op ratio/index/decay), noise (LFSR/short). Per voice: sweep, vibrato, chip arp, glide, envelope, filter, echo, pan, energy gate |
| **Drums** | 13 patterns + `auto` (derived from the meter's grouping) + custom step grids. Hits are X accent, x, o ghost, r roll. Kit pieces: kick, snare, clap, hats, düm, tek, tom, rim, crash |
| **Music styles (12)** | starting points (`bitloop list styles`). Hicaz/maqsum is one of them, not the default |
| **Transitions (17)** | cut crash dissolve whip slide push mosaic iris (eye-shaped) tiles (çini) glitch match silhouette flash spin (`over:true`: no black gap) split portal crt (`floor:0..1`: dim after-image, no near-black frames). Each is beat-aligned (`center` puts the switch on the beat) and gets an automatic SFX |
| **Archetypes (8)** | scale_journey countdown_top_n before_after_reveal process_timeline myth_vs_fact cosmic_zoom_out impossible_number story_vignette (+ blank, reference) |
| **Scenes / layers / props** | as in v1 (`bitloop list scenes|props`); every scene gets ≥ 3 moving layers by default. Music/math pack: `fractal_staff` (play / nest / every4, converge_to_frame0), `koch`, `noise_scope`, `series_tree`, `shepard_stairs`, `mandel_zoom`; object kind `vinyl` (legible label). Story pack (`scenes_story.py`): `future_book` (read / avoid / open), `laplace_demon`, `dominoes` (+ `split`), `libet_clock`, `future_tree` (dice / burst); object kind `book` (legible: title + 2-line handle on the cover). Sync pack (`scenes_sync.py`): `pendulum_grid` — `rows×cols` Kuramoto-coupled pendulums on the GLOBAL beat (chaos → waves → converge → lock), one detuned 17:16 outlier that never locks, coral ring at `outlier_ring`, order-parameter formula at `formula`, freeze at `freeze`; `sfx()` returns `tick`/`tick_hi` at the pendulum peaks (chaotic polyrhythm → coherent). Sprites (`sprites.py`): the mascot hero `HERO` (front blink look_l look_r read wow walk1-3 turn) via `draw_sprite` / `hero_frame` |

## Narration text (narration.py) and pacing
Full-sentence text blocks per segment (`segments[].narration`), revealed on the music grid. Each letter, word or line appears at `start + lead + step·rate` beats, and the soft `blip` SFX are timeline events at exactly those beats (8.7 s smoke test, measured on the encoded mp4: 93/95 letters appeared in the predicted frame. The 2 misses were detector artefacts: the first letter during the box dither-in, and a comma. Blip onsets sat at a constant +7 ms AAC offset with ≤ 0.2 ms jitter, mixed ≈ −28 dB under the music).
- Places: `top` `dialog` (speaker tab, ▼) `panel` `title` `mid` `callout` (leader to `target`) `world` (`surface` in scene coords: sign, screen, book page, chalkboard) `auto`.
- Sizes: `body` 6 px/dot (≈ 24 chars, ≤ 5 lines), `head` 9 (≈ 15, ≤ 3), `title` 12. Measured floor `MIN_DOT = 5` (22′ cap height on a 5.4" phone at 35 cm). `narration.min_legible_dot()` re-derives it.
- Reveal `type|word|line|fade|none`, rate `auto|32nd|16th|8th|beat|half|<beats>`, pauses after punctuation, cursor, `hold`, exit `dither|wipe|cut`, `case` `as_is|upper`, highlights `*türkuaz*` `_mercan_`.
- Auto-layout stays out of the UI safe zones (bottom 18 %, right 12.5 %, left/top 5 %), avoids the subject box and other text, and stacks simultaneous blocks. The first block of a loop returns at the seam so frame T = frame 0.
- `pacing`: `calm` (default) has shake 1.0, flash .22, punch .05, crash 2 beats ×3.5, layers at 60 % speed and default transition lengths ×1.6. `punchy` keeps the old values. A dict such as `{"preset": "calm", "layer_speed": .8}` overrides single values. Full table: recipe §12.7.

## Vision system (vision.py, scenes_vision.py)
"Same world, another eye." A vision segment draws its world ONCE as a G-buffer and maps it through a creature's eye:
- **Aux planes** on the canvas (`cv.enable_aux()`): `uv` (UV reflectance 0..1), `temp` (heat 0..1), `depth` (0 near … 1 sky) and `oid` (object id, 0 = sky). Scenes write them with `cv.put_aux(mask, uv=, temp=, depth=, oid=)` (set `writes_aux = True`). Everything else gets stage defaults: uv .3·lum, temp .2, depth back 1.0 / scene .5 / mid .5, a unique oid per prop (+ 4 luminance steps, so painted letters become sonar edges).
- **Order:** back layers, back props, scene, mid props → G-buffer (albedo in `world_palette`) → vision map → in-world narration, front layers + front props in the mode palette → vignette / flash / shimmer → Bayer quantise to the mode palette (`pixel: 2` = 2×2 acuity blocks). Captions and narration are composited later at full resolution in the brand colours, so text never changes with the eye.
- **Spec:** top-level `visions: {mode: {map, palette, pixel?, blur?, label, ...}}` and `world_palette`; per segment `vision` (a mode, or a plain palette name such as `hayret` = map `rgb` in that palette) and optional `palette` (overrides the output palette of any segment, vision or not). `params.peek {at, beats, mode}` = an ordered-dither blink into another eye; `params.collapse {from, beats}` = dither-dissolve from another eye at the segment start; `params.sonar {origin, rings_on: "drum:B", persistence_beats, speed, max_rings, base}`.
- **Maps:** `rgb`, `bee_false_colour` (R←.82G+.18R, G←.95B, B←UV), `dichromat` (Machado 2009 deuteranopia, γ 2.2), `thermal` (gaussian heat → ramp + 18 % eye image), `sonar` (Sobel depth ∪ oid edges + iso-depth contours lit by rings from every drum-`B` hit; ≤ 3 rings, 300 art px/beat, 1.5-beat persistence), `bands12` (12 hue bands, UV band), `coarse_classes` (5 flat classes), `tint` (lum-tinted night).
- **Transitions** between two eyes render both frames, each in its own palette, and blend them on a union palette (both sides stay palette-exact).
- **One world:** `vision_world` animates from the GLOBAL beat with an integer number of cycles per film (wind, clouds, water, bee track, bat, mouse, shrimp, fish, butterfly), so consecutive segments are eye switches of the same moment and the loop seam is exact. `vision_world` params: `time` day|dusk|night, `focus`, `uv_glow`, `dog`, `snake`, `underwater`, `bat_close`, `bee_keys`. Anchors for callouts / sonar: flower ball mouse bat shrimp hive hive_label bat_hive bee.
- `vision_mosaic`: 2×3 tiles of the same live world through six eyes (`tiles`, `crop` box or `"flower"`, `stagger_beats`, `lead` tiles already in on frame 1, empty slots = first eye dimmed, `sonar_base`), 1-px Kutu gutters; a `final` scene (quantises each tile itself).
- **Brand prop:** `plate` with `skin: "hive"` = painted wooden label (two-line handle, snapped: 6 output px per dot at zoom < 1.75, board sized from the snapped text).
- **Music hooks:** drum `B` (bat chirp, FM 4→1.5 kHz, 18 ms), multi-bar drum grids (length = k × steps per bar), `music.drum_hits(spec, inst)` / `Film.drum_hits(inst)` for picture sync, `pad.max_notes` (default 4, > 4 notes at 1/√n), clusters run through all tones on `up`/`down` arps, one-note chords no longer crash the bass.
- New layer `pollen` (sunlit motes).

## Cosmos pack (scenes_cosmos.py, scenes_chalk.py, sprites_kid.py; evren-anlamak)
- **`cosmic_zoom`**: a powers-of-ten zoom done by the SCENE (camera stays at 1.0). It has five rigidly nested stages: kid on a hill at night → earth (per-pixel lit sphere, fbm continents, dusk band, city lights, moon) → solar system → spiral galaxy → cosmic web. Each stage is ×10 smaller than the next (`chain(Z)`: Q₍ⱼ₋₁₎ = 10(Qⱼ − Aⱼ)). A stage dither-crossfades out once it is smaller than `fade[0]` (1/8) of the frame. Screen-space dark-matter haze (`haze`, dim ramp) and twinkling stars sit behind it. The kid sprite (`sprites_kid.KID`: front, up, q, front_blink, wow, up_blink; 20×24, role colours snapped to the palette) and a scalable telescope + tripod sit on the hilltop.
  - Params: `from`/`to` (stage names, `ease`), `stages:["sky"]` + `constellations:"equations"` (E=mc², F=ma, G_μν=8πT_μν drawn star to star over `draw_beats`), `kid_turns` (close-up turn over `turn_beats`, hayret-eye glint at `eye_glint_at`), `rewind_to_frame0` (`rewind_from: "close"` pulls back from the close-up to the frame-0 shot; `"web"` rewinds the whole zoom).
  - Every motion runs on the global beat with an integer number of cycles per film, so the loop seam is exact.
- **`chalk_unify`**: ONE classroom chalkboard across consecutive segments. The scene finds its run in `bind()`, and later segments only add writing.
  - The slate is drawn in the palette's `board` ramp, with a wooden frame, tray, eraser smudges, desk, books and globe. Chalk handwriting comes from `chalk_blit` (column-by-column writing with a chalk tip, slant, wobble, grain). `left`/`right` formulas use `formula_bitmap` sub/superscripts. `merge_at` slides them together with a puff into `merged` ("? = ?").
  - Other params: `corner_note` (wiped at the next segment); `mode:"calendar"` with `year` + `odds`, or `year_from`→`year_to` page flips over `flip_beats`; `odds_crossout_at` + `godel_note`.
  - `tag: subtle|legible` paints the channel handle in chalk. Legible tags are pixel-snapped and exempt from glow and vignette. They are counted by the brand validator through `brand_tags()`.
- **`galaxy_chess`**: an 8×8 board (`c1`/`c2`) with galaxy chess pieces (P dwarf, R E0, N irregular, B edge-on, Q spiral, K barred spiral) playing the Italian opening, one move every `move_every` beats.
  - `ca_rule` lights one generation per row. With `ca_series` the lights are taken from the music series voice: gen g = notes 4g..4g+3, value = column, lit at the exact note beat. The board is the score.
  - `zoom_out_boards`: a per-pixel LOD renderer of a 512-wide rule-30 universe with the live board at its apex, pulling back `levels` powers of 8. Boards of boards come with their own pieces, and the Sierpiński-like triangle "computes" downward.
  - `counter {from,to,beats,hold,xy}`: "10ⁿ" in the caption box + highlight colour, which hands over to a title block.
- **`laplace_demon` + `chaos_twin {dx, diverge_at, split_px, bumper_every, readout}`**: Sinai billiard twins. Bumpers are placed so ball A grazes one every `bumper_every` beats. Reflections are exact (sub-step), and a bisection on the initial offset makes the twins separate by `split_px` art px exactly at `diverge_at`.
  - Dashed predicted paths are shared until the split, then fan apart in türkuaz and mercan. A gap line and a `FARK 0,0001…` readout show the gap. Half the eyes follow each twin.
- **Engine additions**:
  - pixfont superscripts ⁰¹²³⁴⁵⁶⁷⁸⁹⁻ (`pixfont.SUPERSCRIPT`), plus Greek and calculus glyphs μ ν π ψ ∂ ħ ρ λ Λ Ĥ.
  - `bitmap.formula_bitmap("G_{μν}")` and minifont `,`.
  - Arp `pattern:"random"` (seeded, beat-anchored, never the same pitch twice in a row); unknown arp/bass patterns now warn.
  - `sprites.snap_colour` / `draw_sprite(roles=, snap=)`; scene class attributes `own_layers` (counted by the layer rule) and `brand_tags(params)`.
  - The `chalkboard` prop uses the `board` ramp.
  - `cli --package` reads `meta.cover_t`.
  - The encoder writes bt709 tags + an `h264_metadata` bsf on every render.
- Tests: `tests/test_cosmos.py` (17, incl. the QC v2 phone-legibility / pose-continuity test).

## Validator (brand + quality, no fixed template)
- **Errors:**
  - Unfilled slots.
  - Unknown scene, transition or scale; an unknown `vision` / peek / collapse mode or map; a bad segment `palette`.
  - Fewer than 3 layers in a scene.
  - Caption over 3 lines or shrinking below the legible 5 px/dot; narration below 5 px/dot; a glyph the font lacks.
  - The handle used in a caption or narration block. Unknown narration place/reveal/exit/rate.
  - The tag never legible.
  - No hook caption or narration in the first 2 s.
  - Duration outside 15–90 s.
- **Warnings:**
  - Hook text later than 1.5 s or not fully revealed by ~3 s, or no curiosity gap in the first 3 s.
  - **Readability:** a block (or caption) that leaves < 0.6 s + 0.35 s/word after its full reveal (`readability` tunes it); more than 5 body / 3 head lines; a reveal off the music grid; a block covering > 30 % of the subject, leaving the UI-safe area or overlapping other text; in-world text below 5 px/dot on screen.
  - **Pacing (calm):** static stretch > 4.5 s (text reveal counts as a change; held breath ≤ 1.5 s exempt), average visual change outside 1–3.5 s, shots averaging < 2.5 s, more than ~1 fast transition (crash whip spin glitch flash mosaic portal split) per 10 s, fast cameras outside the hook, shake > 2 / flash > .4. `punchy` keeps the old 3 s / 2.5 s rules.
  - A re-hook gap over 8 s, no twist at 30–80 %, or no payoff in the second half.
  - Energy that doesn't escalate.
  - Fewer than 3 transition types, or 3 identical transitions in a row.
  - A cut off the ½-beat grid.
  - Duration outside the 20–45 s sweet spot. (The old 12-char / 6-word caption rules and the 25–60 % text-coverage rule are gone.)
  - More than 3 tags, or a tag in the first 2 s.
  - Tempo outside 60–180 BPM.
  - Title or hashtag count out of range.
- `validate` also prints the **RETENTION MAP**: a lane strip (0.5 s per character) plus the event table, the average visual-change interval, the longest static stretch and the longest re-hook gap.

## Files
```
bitloop/  timing.py (Meter, TempoMap)  theory.py (scales, makams, chords, motifs)  voices.py (chip voices, flavours)
          drums.py (patterns, kit)  sfx.py (SFX palette)  music.py (arranger, styles, sonic logo, mastering)
          transitions.py  spec.py (normalise, pacing presets, events, validator, retention map)  archetypes.py
          narration.py (narrator text: legibility, Turkish wrap, reveal timing, blips, layout, compositing)
          render.py  scenes.py layers.py props.py raster.py palette.py captions.py pixfont.py bitmap.py shapes.py cli.py
          scenes_music.py (fractal_staff noise_scope series_tree shepard_stairs)  scenes_math.py (koch mandel_zoom)  minifont.py (3×5)
          scenes_story.py (future_book laplace_demon dominoes libet_clock future_tree, book object)  sprites.py (mascot hero)
          vision.py (vision maps, quantise, dither mix, union palette)  scenes_vision.py (vision_world vision_mosaic)
          scenes_cosmos.py (cosmic_zoom galaxy_chess)  scenes_chalk.py (chalk_unify)  sprites_kid.py (stargazer kid)
          templates/blank.json  templates/reference_scale_journey.json (the analysed reference as a spec)
tests/test_engine.py  tests/test_fractal.py  tests/test_story.py  tests/test_narration.py  tests/test_vision.py  tests/test_cosmos.py    bitloop.sh
```

## Limits / honest notes
- **Synth:** original chiptune, no samples. Makam microtones are simplified approximations (no full AEU koma system), and pitch bends/çarpma ornaments are not modelled.
- **Composition:** rule-based (seeded motifs, diatonic harmony). Good-sounding and varied, but not a human composer; listen to every soundtrack and tweak the motif or voices.
- **Transitions:** they work on the rendered art frame (nearest-neighbour), so `spin`, `portal` and `whip` briefly scale pixels. Camera zooms still redraw geometry.
- **Validator:** visual-change detection counts cuts, transitions, events, captions, narration reveals (one change per second of reveal), scene events, big camera moves and late props. Continuous particle motion is not counted, so it is deliberately strict.
- **Narration:** layout avoids a simple per-scene subject box (focus ± 40 units or `segment.subject`), not real silhouettes. Hyphenation uses the native Turkish syllable rule, so loanword clusters split natively (`elekt-rik`, not `elek-trik`). Lowercase is 5×7 with one-row descenders.
- **Vision:** the maps are honest translations, not experiences: false colour (bee), a deuteranope simulation (dog), heat (snake), an echo picture (bat). Front layers (dust, pollen) are drawn in the eye's palette after the map ("eye floaters"); the vision pass costs ≈ 0.3 s per art frame on one core (two maps during a peek/collapse).
- **Scenes:** still generic motifs. Topic subjects need PNG silhouettes or new scene functions.
