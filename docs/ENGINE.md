# ENGINE: bitloop module map and spec key fields

`bitloop` (in `bitloop/bitloop/`) turns a spec (JSON) into a finished reel: 1080×1920, 30 fps, H.264 + AAC, −14 LUFS.
Pure Python + numpy (+ scipy for filters/vision, Pillow for images) + ffmpeg. Deterministic (seeded); `Film.frame(t)` is a
pure function of time, so frames render in parallel worker processes.

- **Full reference** (every param, libraries, limits): [`../bitloop/README.md`](../bitloop/README.md).
- **Authoring guide** (how to design music + edit per topic, retention playbook, narration, calm pacing, vision, cosmos pack;
  Turkish): [`../recipe/recipe.md`](../recipe/recipe.md) **§12**. JSON schema: `recipe/recipe.json` → `spec_schema`.
- Live listings: `bitloop/bitloop.sh list archetypes|styles|scales|drums|transitions|props|scenes`.

## Pipeline
```
spec.json ─ spec.load ─ normalise (preset "hayret" + pacing + tempo map + sections + segments: beats → seconds)
          ├ spec.validate / retention_map ............ errors, warnings, RETENTION MAP (validate command)
          ├ music.build_audio ......................... synth(voices, drums, series, sonic logo, SFX from timeline_events)
          │                                             → loudnorm (two-pass −14 LUFS, HF shelf, AAC-safe limiter) → wav
          └ render.Film.frame(t) ...................... layers → props → scene → camera → transitions → vision map →
                                                        narration/captions → palette quantise (Bayer) → ×6 nearest → ffmpeg
```
One clock: **1 beat = 1 quarter note** everywhere; `timing.TempoMap` integrates bpm (with `bpm_to` ramps, meter changes).
`spec.timeline_events()` is the single event list feeding SFX, shake/flash/punch and the retention map.

## Modules
| Module | Role |
|---|---|
| `timing.py` | `Meter`, `TempoMap`: beats ↔ seconds across tempo ramps and meter changes (7/8 = 3.5 beats). |
| `theory.py` | 23 scales incl. makams (hicaz, uşşak, kürdi, nihavend, rast, hüzzam, saba; `tuning: "approx"` microtones), chords, roman-numeral progressions, motif generator. |
| `voices.py` | Chip voices (pulse/PWM, 4-bit triangle, saw, Game Boy wavetable, 2-op FM, LFSR noise) and flavours `2a03`, `gameboy`, `sid`, `fm`; per-sample pitch curves (vibrato, sweep, arp, glide). |
| `drums.py` | 13 step-grid patterns + `auto` (aksak accents from the meter grouping) + custom grids, multi-bar grids, kit incl. düm/tek and bat chirp `B`. |
| `sfx.py` | SFX palette; every event/transition maps to one (remap/mute with `music.sfx`); narration blips. |
| `music.py` | Arranger: styles (12 starting points), roles (lead counter arp bass pad), sections (energy, stop, drop, riser incl. Shepard, key/scale/bpm changes, `level_db`), integer-series voices (`series`, `series_defs`, `lookahead`), sonic logo, `loudnorm`, `build_audio`. |
| `transitions.py` | 17 beat-synced transitions: cut crash dissolve whip slide push mosaic iris tiles glitch match silhouette flash spin split portal crt. |
| `archetypes.py` | 8 optional structure skeletons (scale_journey, countdown_top_n, before_after_reveal, process_timeline, myth_vs_fact, cosmic_zoom_out, impossible_number, story_vignette) used by `init`. |
| `spec.py` | Load/normalise, brand `PRESETS`, `PACING` (calm/punchy), auto brand placement, events, validator, retention map. |
| `render.py` | `Film` (frame compositor), `render` (parallel workers → ffmpeg, bt709 tags), `still`, `sheet`. |
| `raster.py` | Art-resolution rasteriser with redraw camera, glow buffer, aux G-buffer planes, `Canvas.keep` (glow/vignette-exempt pixels). |
| `palette.py` | Locked palettes (`hayret` = Çini Gecesi, `violet-amber` = reference, `teal-coral`; topic palettes come as dicts from the spec, e.g. `projects/evren-anlamak/palettes.py`) + Bayer 4×4 quantisation. |
| `layers.py` | Parallax backdrops (horizon nebula stars tiles grid skyline rays) and foreground particles (bokeh debris dust pollen); `DEFAULT_STACK`. |
| `props.py` | Diegetic brand props: neon_sign billboard plate patch ship terminal chalkboard stamp. |
| `narration.py` | Narrator text: legibility floor (`MIN_DOT = 5`), safe zones (`SAFE`: bottom 18 %, right 12.5 %, top/left 5 %), Turkish wrap + hyphenation, reveal timing on the beat grid, blips, layout (top dialog panel title mid callout world auto), reading-time rule. |
| `captions.py` | Legacy short ALL-CAPS top captions (still supported, used by the first two reels). |
| `pixfont.py` | **Built-in 5×7 pixel font with full-height Turkish capitals** (İ Ş Ğ Ü Ö Ç Â Î Û), lower case, superscripts, Greek/calculus glyphs, the hayret eye `MARK`. |
| `minifont.py` | 3×5 micro font for tiny in-world labels (Turkish-aware upper-casing). Not for text that must be read on phones. |
| `bitmap.py` | World-space bitmaps (text, logo, `formula_bitmap("G_{μν}")`) with rotation and `snap=True` pixel-exact stamping. |
| `shapes.py` | Masks for silhouettes: built-in shapes, `glyph:X` from the pixel font, or a PNG. |
| `sprites.py`, `sprites_kid.py` | Char-map sprites: hooded hero "Kâşif", stargazer kid "Meraklı" (palette-snapped roles). |
| `scenes.py` | Generic scenes: hero lattice chain streaks pod junction network silhouette object image void. |
| `scenes_music.py`, `scenes_math.py` | fractal_staff noise_scope series_tree shepard_stairs · koch mandel_zoom. |
| `scenes_story.py` | future_book laplace_demon (+ `chaos_twin`) dominoes libet_clock future_tree. |
| `vision.py`, `scenes_vision.py` | Creature-vision maps over a G-buffer (uv, temp, depth, oid): `rgb bee_false_colour dichromat thermal sonar bands12 coarse_classes tint` (thermal tiles get AGC in the mosaic); vision_world, vision_mosaic. |
| `scenes_cosmos.py`, `scenes_chalk.py` | cosmic_zoom (powers of ten done by the scene, `rewind_to_frame0`), galaxy_chess (+ rule-30 `ca_series`, boards of boards) · chalk_unify (one persistent chalkboard across segments). |
| `scenes_sync.py` | `pendulum_grid`: rows×cols Kuramoto-coupled pendulums on the global beat (chaos → waves → converge → lock), one detuned 17:16 outlier that never locks, coral ring + order-parameter formula + freeze; `sfx()` emits `tick`/`tick_hi` at the peaks. |
| `cli.py`, `__main__.py` | Commands: `init list validate info music still sheet strip render [--draft --crf --range --package]`; `cover_t()`. |
| `templates/` | `blank.json`, `reference_scale_journey.json` (the analysed reference as a spec). |

Tests (`bitloop/tests/`, 79): `test_engine` 14 · `test_fractal` 12 · `test_story` 10 · `test_narration` 10 · `test_vision` 10 · `test_cosmos` 17 · `test_sync` 6.

## Spec key fields (see bitloop/README.md "Spec at a glance" for a full example)
| Field | Meaning |
|---|---|
| `version: 2`, `preset: "hayret"` | Brand layer (palette, logo, handle `@hayret.piksel`, auto tag placement). |
| `pacing` | `"calm"` (default) or `"punchy"`. |
| `meta` | `title`, `description`, `hashtags` (3–6), `lang: "tr"`, `cover_t` (seconds). |
| `format` | Defaults `width 1080, height 1920, fps 30, grid 6`. |
| `palette` | Name or `{colors: [...] , ramps…}`; segments may override with `segments[].palette`. |
| `music` | `style?`, `bpm`, `meter`, `grouping`, `key`, `scale`, `tuning`, `flavour`, `progression`, `chord_bars`, `swing`, `seed`, `voices{name:{role,type,…, series?}}`, `series_defs`, `drums`, `motif`, `sections[]` (`name`, `bars|beats`, `energy`, `bpm_to`, `key`, `scale`, `voices`, `voices_in/out`, `drums`, `fill`, `riser`, `riser_kind`, `stop`, `drop`, `level_db`), `logo{at}`, `sfx{}`, `lufs`, `hf_shelf_db`, `limit_ceiling`, `breath`. |
| `segments[]` | `id`, `role` (hook promise step build hold drop hit rehook number twist reveal payoff metaphor system contrast loop free), `scene`, `beats|bars`, `params`, `layers{back,front}`, `props[]`, `camera{zoom,pan,rot,orbit,ease}`, `transition_in`, `narration[]`, `caption`, `events[]` (punch shake flash pulse pop rehook twist reveal mark), `subject`, `vision`, `palette`, `layer_sync`. |
| `narration[]` block | `text` (`*türkuaz*`, `_mercan_`, `\n`), `at`/`until`, `place`, `size`, `reveal`, `rate`, `blip`, `cursor`, `exit`, `case`, `xy`, `speaker`, `target`, `surface` (recipe §12.6). |
| `narration_defaults`, `readability` | Defaults for all blocks; reading-time rule `{"base": .6, "per_word": .35}`. |
| `visions`, `world_palette` | Creature-vision modes (recipe §12.9). |
| `brand` | `handle`, `auto`; tags can also come from props / scene params (`tag: "legible"`). |
| `loop`, `loop_transition`, `loop_beats` | Seamless loop seam (sonic logo plays there). |

## Extending the engine (rules)
1. New params **default to the old behaviour**; old projects must render identically. 2. Add a test in `bitloop/tests/`
(run the whole suite). 3. Frames stay pure functions of `t` (global beat), with an integer number of cycles per film for
anything that must loop. 4. Stay palette-exact (no off-palette blends), pixel-snapped text, nothing in the safe zones.
5. Document it in `bitloop/README.md` and recipe §12 (and here if it is a new module).
