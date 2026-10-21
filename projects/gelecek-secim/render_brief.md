# Render brief: gelecek-secim (for the render/coder worker)

- **Target:** `spec.json`. Generate it with `python build_spec.py (repo venv active)`; edit that file, not the JSON.
- **Validation today:** `bitloop validate spec.json` fails only with:
  - "unknown scene" for the 5 new scenes
  - "unknown series" for `kehanet` / `kacis`
  - "tag never legible", because the object kind `book` isn't registered yet
- **Proxy:** `spec_proxy.json` uses the same timeline with existing scenes and a plain motif. It validates **OK** today with 0 warnings and produced `storyboard.png`. That board is timing/captions only; its art is placeholder.
- **Timeline:**
  - 120 BPM, 80 beats = 40.0 s.
  - Meter map: 4/4 for beats 0–40, 7/8 [2,2,3] for 40–68, 4/4 for 68–80.
  - Phrase grid: the kehanet phrase is 8 beats and restarts at beats 0, 8, …, 40. The twist (beat 40) and the loop seam (beat 80) both land on a phrase start.
  - Cuts in the 7/8 part land on half-beats (allowed grid).

**QC lessons applied from fraktal-muzik** (please keep):
- **Lower third:** every scene puts content in the lower third (fork road + prophecy roll, billiard table, domino run, EEG strip, branch roots, desk).
- **Text size:** no text under 2 dots. Small labels use `snap=True`. Nothing readable sits on a layer that zooms > 1.5×.
- **First frames:** no empty first frame. Every scene's `lb=0` state is already populated (pre-roll the simulation, don't grow from nothing at t=0).
- **Phone mix:** bass is a pulse wave at octave 3, no sub. `hf_shelf_db: -3`.
- **Readable metaphors:** concrete objects (book, arrow, dominoes, dice, clock).

---
## A. Engine features (music)
1. **List series from the spec.** `music.series_defs: {name: {values: [ints], period: N}}`.
   - Register these into `theory.SERIES` at spec load, so music and visuals share them. Value at index i = `values[i % period]`.
   - Validator: accept names defined here.
2. **Series `lookahead: k`** (voice `fisilti`). At slot n, play `value(n+k)`; the voice is literally one note in the future.
   - Index stays on the global grid, so in the 7/8 sections it keeps whispering the **kehanet** notes while `kacis` plays the avoider line. That audible mismatch is the point of the twist; don't "fix" it.
   - Duck the whisper by 50 % under the logo windows.
3. **Phase `section` for `kacis`** (exists). Check that `kacis` restarts at beat 40 (S6) and beat 54 (S8).
4. Voice-level `filter: "soft"` on bass/pad if it isn't already supported for pulse/saw. Otherwise drop it.
5. **Listen checks** (`bitloop music spec.json -o music.wav`):
   - The **tick-tock** is clear on a phone: rim on beats, tek on off-8ths, the kick soft.
   - At **21.5 s** (beat 43) the whisper predicts high E while the line goes to C: it should sound like a "wrong-foot", not a mistake. If it's too dissonant, lower the whisper to −8 dB only in `kacis`.
   - At the loop seam, the logo's long G is over the whisper's E.

## B. New scenes
### 1. `future_book` (S1 read, S6 avoid, S10 open → loop): the hero scene
- **Character:** a hooded pixel hero, ~28×40 art px at `sprite_scale` 2. Cream face with two dark eye pixels and a cobalt cloak with a lapis rim light. 4-frame idle bob on beats and a 4-frame step/turn cycle.
- **Book:** held at chest height and opening toward camera. The pages are cream with a dither shadow, and turn every `page_flip_every` (0.5 beat) with a 3-frame flip.
  - The right page shows ONE big arrow glyph (≥ 12 dots tall, Türkuaz Işık) pointing `arrow`.
  - A tiny pixel portrait of the hero sits under the arrow. No small text on the pages.
- **Fork road** (`fork`), lower 35 % of frame: a dirt path splitting into LEFT and RIGHT branches in perspective, each ending in a glowing doorway. Lamps along the paths blink on 8ths.
- **Prophecy roll** (`roll`, `roll_series`): a one-row piano-roll strip at y≈+120, about the bottom 12 %.
  - **Ghost** notes (Mürekkep outline) show the next 8 values of the series, lane = degree.
  - The note crossing the playhead fills Türkuaz on its exact 8th, using the same `series_index(beat, 2)` formula.
- **`read`:**
  - At `step_at` (beat 3) the hero steps onto the left branch, matching the arrow.
  - Over beats 6.8–8 the camera's crash target is the arrow, so `focus` returns the arrow's position.
- **`avoid` (TWIST):**
  - Beats 0–3: the hero reads; the arrow glows left.
  - At `turn_at` 3 the hero pivots and walks RIGHT. The arrow cracks (3-frame coral fracture, `ink_crack_at`). On the roll, the predicted ghost note at that slot turns into a coral ✗, and the actually played `actual_series` (kacis) note lights in a different lane.
  - Add small shake + pop.
- **`open` + loop (S10):**
  - Starts from the closed book cover (matches the end of S9 via the `match` transition), opens over 2 beats, and settles into **exactly S1 frame 0**: same page phase, hero pose, roll phase (wrap at 80 beats), camera.
  - QC will diff the first and last frames.

### 2. `laplace_demon` (S2)
- A many-eyed pixel creature (`eyes` 9): a dark cobalt blob with eyes that are small hayret-eye shapes (cream, türkuaz iris, coral pupil). It looms in the upper half; eyes blink on random beats (seeded).
- Below it, a **billiard table** (felt Firuze dark, cream cushions) fills the lower third with `balls` 7 balls. The simulation is real and deterministic: elastic bounces with fixed seed and pre-rolled 2 s so frame 0 is mid-motion.
- **`paths`:** each ball shows its future trajectory as a dotted Türkuaz line for the next 2 beats, computed from the same simulation, so the ball really follows its predicted line.
- Every `path_reveal_every` beat a new ball's path lights. Collisions fire a `tick` on the nearest 16th; nudge the sim timing to land collisions on the grid where possible.
- **`abacus`:** a small pixel abacus/number column the demon "counts" on, beads sliding on beats. Decorative, no text.
- `focus` = the demon's central eye (S1 crash lands here).

### 3. `dominoes` (S3, S4)
- `n` dominoes in a perspective line running from the lower-left foreground into the distance. Cream faces with pips, Gece shadow.
- One topples every `fall_every` (0.5 beat) with a 4-frame fall and a `tick` SFX. Pre-roll so 4 are already down at frame 0.
- **`clock` / `pendulum`:** a giant clock face behind (Kobalt with cream numerals as glyph shapes, not text). Its pendulum swings with a period of 2 beats (tick-tock), hands step on beats.
- A brass `plate` prop on the clock case carries the subtle tag (`model: "LAPLACE-1814"`).
- **`split`** (S4): two halves with a coral divider line.
  - **Top `hard`:** dominoes with closed-eye faces fall mechanically.
  - **Bottom `thinker`:** the same line, but one domino at `thinker_at` (beat 3) opens its eyes, looks left/right (2 beats), then CHOOSES to fall onto a side branch of dominoes. Light Türkuaz on its chosen branch.
  - Both halves stay legible at phone size: big shapes, no text.

### 4. `libet_clock` (S5)
- Upper half: a **Libet clock**, a round cream face with 60 tick marks. A coral spot revolves once per `period_s` = 2.56 s (convert to beats via the tempo map), with a small tail.
- Lower third: an **EEG strip** (CRT green → Türkuaz trace on Gece) scrolling left, plus a big round button that is pressed at `press_at` (beat 3).
- **Trace:** before the press, a smooth negative-going ramp (the RP) starting `rp_onset_ms` = −550 ms. A W marker (coral tick) sits at −200 ms on the clock and on the strip.
- **At `noise_at` (beat 4):** the single smooth ramp splits into `noise_trials` (12) thin noisy traces (seeded autocorrelated noise plus a leaky accumulator that crosses a threshold at the press). Their **average** (thick Türkuaz) re-forms the same ramp. This is the visual of Schurger 2012.
- A `terminal` prop (subtle tag) types `> @hayret.piksel` then `> W = -200 ms`.

### 5. `future_tree` (S7 dice, S8 burst)
- **`dice`:**
  - Two big pixel dice (cream, coral pips) tumble mid-air with a 6-frame rotation cycle, changing face every `roll_every` (0.5 beat) on the grid.
  - Each landing face sprouts a short glowing path downward into the lower third (`branch_from_faces`).
  - A coral ring contracts around the dice from `ring_countdown_from` (3.5).
  - The last 0.5 beat is frozen (held breath).
- **`burst` (DROP):**
  - From the dice point, a branching tree of paths grows explosively, binary-ish with seeded angles. Depth `depth` 6; one generation every `grow_every` 0.5 beat; frame 0 already shows 2 generations.
  - Paths are 2–3 px lines with lamps at the nodes.
  - `walkers` 8: ghost copies of the hero walk different branches. `chosen_path_glow`: one path from root to a leaf burns Türkuaz.
  - `pull_out`: the camera pulls back (zoom 2.2→0.8). Path widths are redrawn per zoom; no bitmap scaling.
  - Shake on beat 0, punch on beats 7 and 10.5.

### 6. `object` kind `book` (S9, the LEGIBLE TAG): add to `LEGIBLE_OBJECTS`
- A thick hardcover book on a wooden desk (`desk`), with a lit candle (`candle`, 3-frame flame, warm Mercan Işık glow).
- **`state: closing`:** the book is open at frame 0 (arrow page visible, as in S6), then closes at `close_at` (0.5 beat) with a thud.
- **Cover** (Kobalt leather, cream embossed frame):
  - hayret eye emblem on top
  - `title` "GELECEĞİN / KİTABI" in cream, 2 dots, snapped
  - at the bottom, a publisher line **`@hayret` / `.piksel`** in Türkuaz Işık or cream on dark: ≥ 2 dots, snapped, contrast ≥ 7:1, upright, matte (clear glow under the text)
- `brand_at` 1.0, simultaneous with the sonic logo long note.
- Dust motes in the candle light.

## C. Transition notes
- **S2 crash:** dives into the book arrow (S1 `focus`).
- **S4 split:** the split transition's top/bottom should match the scene's own split (old S3 top stays where S4 "hard" top is).
- **S6 iris (hayret eye):** opens on the hero's face reading.
- **S7 spin:** `over: true`.
- **S10 match:** from the closed cover to the cover in `future_book` `open`.

## D. Checks before QC
- [ ] `validate spec.json` → OK. Expected: no warnings (the proxy is clean: text 59 %, re-hook gap 5.8 s, longest static 1.75 s).
- [ ] Prophecy-roll lit notes coincide with `saat` onsets. In S6, the ✗ lands on the first slot where the whisper and kacis disagree: beat 43 = 21.5 s, the 7th 8th of the twist, which is also `turn_at` 3. After that the whisper keeps predicting kehanet while kacis plays a new line.
- [ ] S10 last frame ≈ S1 first frame. Audio seam clean.
- [ ] Tags = 3 (plate S3, terminal S5, book cover S9); none in the first 2 s.
- [ ] Mix on a phone speaker: tick audible, bass audible, no harsh highs.
