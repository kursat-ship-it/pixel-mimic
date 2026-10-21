# Render brief: evren-anlamak (for the render coder)

Spec: `spec.json`, built by `build_spec.py`; topic palettes are in `palettes.py`. Proxy: `spec_proxy.json` uses only existing scenes and validates **OK** (one intended warning: 48.0 s > 45 s).
The 9 target errors in `retention_map.txt` are only the unknown new scenes `cosmic_zoom`, `chalk_unify` and `galaxy_chess`.
Timeline: 100 BPM, 4/4, 80 beats = 48.0 s, 30 fps, 1080×1920, grid 6 (art 180×320), pacing calm, cover_t 32.4 s.

**Already supported, used as-is:**
- per-segment `palette` (dict or name)
- narration blocks
- `series_defs` list series + `phase: "section"`
- `sections[].level_db`
- shepard / noise risers, `stop`, `drop`, logo at reveal + loop

## 0. Bug to fix first: `--package` cover
`cli.py` line ~96 does `still(s, s.get("cover_t", 1.0), …)`, but cover_t lives in `meta.cover_t`. So the cover is always taken from t = 1.0 s (QC hit this on canli-gozu).
Fix: `s["meta"].get("cover_t", s.get("cover_t", 1.0))`, then add a test.

## 1. NEW scene `cosmic_zoom` (S1, S8, S9, S10): powers of ten
- `stages`: kid → earth → solar → galaxy → web.
  - Each stage is a full pixel tableau drawn at its own scale.
  - The scene interpolates log-scale between stages: each stage is ×10 smaller than the next.
  - Crossfade with ordered dither when a stage is < 1/8 of the frame.
- **The SCENE does the zoom, not the camera.** Camera stays 1.0, so calm camera rules hold; only the hook is fast.
- S1: `from: kid, to: web` over 8 beats, `inOutSine`.
- S10: `rewind_to_frame0`: a fast reverse zoom web → kid that ends EXACTLY on S1 frame 0 (loop seam).
- **Frame 0 (= cover-able hook frame):**
  - Kid on a hilltop at night, looking up, small telescope.
  - Hill silhouette fills the lower third, but no subject in the bottom 18 %: the kid sits at ~y 0.62 H.
  - Stars twinkle from frame 0, so there is no empty first frame.
- **S8 `stages:["sky"]`, `constellations:"equations"`:** the kid's sky.
  - Stars link into constellations whose lines trace E=mc², F=ma and the field-equation shape.
  - Lines draw over ~4 beats: continuous motion, no dead spot.
- **S9 `kid_turns`:** the kid turns from the sky to the camera (2 beats). At beat 6 a glint in the eye = the hayret eye logo (small, 1 beat).
  - Palette is brand `hayret`, crossfading from Kozmos during the 2-beat dissolve.
- **Dark-matter haze (all Kozmos stages):** a slow noise field in the `dim` ramp (#22284A…#4E6A78) behind the visible stars and galaxies, ~60 % of the screen area.
  - Visual metaphor for the 95 %. Keep it subtle; it must never resolve into shapes.

## 2. NEW scene `chalk_unify` (S2–S4): one board, three segments
- Keep ONE scene instance across S2→S3→S4 (same as the canli-gozu vision continuity), so chalk dust and handwriting continue.
- The slate is drawn by the scene in the `board` ramp (#0C1A14 #12261D #1A3428) with a wooden frame (`accent` #3A2414…).
  - Today's `chalkboard` prop fills with `energy(.08)` and comes out orange-brown in this palette (see palette_board.png). Either read a `board` ramp when present, or let the scene draw its own slate.
- **S2:**
  - Left equation `G_μν = 8πG T_μν`, right `iħ ∂ψ/∂t = Ĥψ`, written in chalk as hand-written pixel glyphs (bitmap sprites are fine; the font lacks Greek).
  - At `merge_at` 6 they slide together and fuse into one line `? = ?` with a chalk-dust puff.
  - Corner note "evrenin %95'i: ?" (decor; the callout carries the readable text).
- **S3 `mode:"calendar"`, year 1980:**
  - Tear-off calendar on the board; "SON: %50" written in chalk.
- **S4:**
  - The calendar flips 1980 → 2002 (pages flutter for 1.5 beats).
  - At beat 2 the "%50" is crossed out with a chalk stroke; "GÖDEL 1931" appears in yellow chalk.
  - **Legible tag:** chalk "@hayret.piksel" in the board's lower-right corner, ≥ 5 px/dot at the S4 zoom (1.14–1.2).
  - S2 and S3 show it small (subtle). Keep the prop entries so the validator counts it, or register the scene's tag.
- **Dialog boxes (S3/S4 "HAWKING, 1980/2002")** sit at the bottom panel; keep the calendar and the board text above them.

## 3. `laplace_demon` (existing): new param `chaos_twin` (S5)
- `balls: 2` = the twins.
- They start 0.0001 apart on identical paths; the dashed predicted paths overlap until `diverge_at` 3 beats, then visibly fan apart.
  - Error amplification: draw the gap growing exponentially, e.g. ×2 per beat, from 0 px.
- Callback reel: the demon's many eyes track both balls.
- Keep abacus off: fewer impact ticks = calm (validator scene-change rate).

## 4. NEW scene `galaxy_chess` (S6, S7)
- 8×8 board in Kozmos tones (cells #140F38 / #1F1752); pieces = tiny spiral or elliptical galaxies, gold/violet.
- `ca_rule:30`:
  - One row per beat lights up, rule 30 from a single centre cell. Rows = generations, 8 cells = 8 files.
  - It must match the music series `kural30` (defined in `spec.music.series_defs`): row `g` lights the cells whose positions are the notes `kural30[4g:4g+4]`.
  - Read the CA from the same function as `build_spec.py: rule_ca()`, or from `spec.music.series_defs`.
- `move_every: 2`: a galaxy-piece slides one move (S6).
- **S7:**
  - `zoom_out_boards`: each square becomes its own board (fractal board of boards), seen while the scene zooms out.
  - `counter`: big digits "10^1 → 10^120" roll in the top third over 4 beats.
  - **Wanted:** a superscript glyph so the narration/title can show "10¹²⁰". Add ¹ ² ⁰ (U+00B9 U+00B2 U+2070) to pixfont; until then the narration says "10 üzeri 120".
- **Transition into S7 = `portal`** (the only fast transition): zoom through one square into the board of boards.
- Subtle tag: none here (3 placements are already used on the board).

## 5. Music: nothing new is required; verify these
- `series_defs`:
  - `kural30` (64 values, 16 generations × 4)
  - `kaos_a` / `kaos_b`: logistic map r = 3.9, x0 = 0.4 vs 0.4001, ×8 → degrees. Identical for the first 12 values, then they diverge.
  - Both are played at rate 2 with phase `section` in `laplace`, so the unison lasts exactly 6 beats.
- Check by ear that the twin bells are in unison for 6 beats, then split. If the fm timbre masks it, raise `saat_b` pan to ±.5.
- `pattern:"random"` on `kuantum`: if this pattern name doesn't exist, use `"broken"`. The proxy rendered fine, so it's either supported or silently defaulted; please confirm.
- Levels via `level_db`: Einstein −4, drop +1.5. Proxy smoke test: −14.1 LUFS, LRA 4.5, peak −4.3 dBFS.

## 6. Narration
All blocks: word reveal at 16th; the S7 title block is at 8th with `xy [0.5, 0.2]`.

| Placement | Segments |
|---|---|
| top | S1 head, S2, S5 |
| callout | S2, target the corner note (world [40, 40]) |
| dialog | S3/S4 HAWKING, S6 FEYNMAN, S8 EINSTEIN |
| title | S7 |
| panel | S7 second block, S9 |

Re-run `validate spec.json` once the scenes exist (layout and subject overlap). The S1 subject box `[-24, 40, 24, 90]` = the kid.

## 7. Acceptance checks
1. `validate spec.json`: 0 errors, only the duration warning.
2. No segment has a stretch > 2 s without visible motion. QC flagged a near-static S4 last time; here S4 has the calendar flip plus the crossout.
3. S7 CA rows light up within 1 frame of the `kural30` generation beats.
4. S5 twins split at beat 3 ± 1 frame.
5. Loop: last frame == frame 0.
6. Cover written from 32.4 s (after the cli fix).
7. No text in the bottom 18 % / right 12.5 %. Bass audible on phone; flash ≤ .35.
