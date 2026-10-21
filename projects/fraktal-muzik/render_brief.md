# Render brief: fraktal-muzik (for the render/coder worker)

- **Target spec:** `spec.json`. It uses the NEW scenes below, so `bitloop validate` currently fails only with "unknown scene" plus "tag never legible" (the `vinyl` object kind isn't registered yet).
- **Proxy:** `spec_proxy.json` is the same timeline with existing scenes. It validates **OK** today and produced `storyboard.png`, a timing/caption board only, with placeholder art.
- **Regenerate both** with `python build_spec.py (repo venv active)`. Edit `build_spec.py`, not the JSON.

Timeline: 100 BPM, 4/4, 70 beats = 42.0 s, 10 segments. Brand constants as usual (Çini Gecesi, ≥3 moving layers, 30 fps, captions top box).

**Single source of truth for melody AND visuals:** Nørgård infinity series
```
a(0)=0; a(2n) = -a(n); a(2n+1) = a(n) + 1      # 0 1 -1 2 1 0 -2 3 -1 2 0 1 2 -1 -3 4 ...
```
Range over the first 280 terms: −7…+8. Put it in `theory.py` as `norgard(n)` and use it in BOTH music and scenes. Note index at global beat `b` for a voice at `rate` notes/beat = `floor(b*rate)`. Visual note-lights must use the same formula, so sync is automatic.

---
## A. Engine features (music)
1. **Per-voice `series` generator** (voices.*.series = `{name:"norgard", rate, sign, phase:"global"}`)
   - Note at every `1/rate` beats on the **global** beat grid. Do not restart per section; this is critical for the self-similarity.
   - Degree = `sign * a(floor(b*rate))`, as an **absolute scale degree** from the section key (ignore chord degree), at the voice's `octave`. Duration = `0.92/rate` beats.
   - Works for any role: lead/counter/bass/pad. For `bass` it overrides `pattern`.
   - Respects section `voices` activation, `silent()` (drop breath / stop), and the logo windows.
   - Section `scale` changes apply: the drop/answer sections are G lydian.
   - **Why it sounds good:** counter (rate 2, sign −1), bass (rate 1), lead_q (rate 1) and sub (rate ¼) always hit the **same pitch class** as the 16th-note lead at their onsets, because a(2n)=−a(n), a(4n)=a(n), a(16n)=a(n). Please unit-test that equality.
   - Current fallback: global `motif` = 64 terms at 16ths. Since progression is static `["i"]`, the lead is already correct with today's engine, but it restarts each section. Replace it.
2. **Shepard–Risset riser:** section flag `riser_kind:"shepard"` (S7, beats 40–48), replacing the default noise riser.
   - 6–7 octave-spaced partials (G1…G7), pulse duty 0.5 / triangle mix.
   - Each partial's amplitude = Gaussian over log2(f), centre G4, σ ≈ 1.2 octaves.
   - Stepped chromatically **one semitone per 16th** (chiptune-style Shepard scale), so 32 steps over 8 beats. Each partial wraps from top to bottom invisibly.
   - Crescendo 0→1 over the section, plus a thin noise sweep on top in the last 2 beats.
   - Then the usual `stop: 0.5` held breath before the drop on beat 48.
3. **Schema/validator:**
   - Add `series` (voice) and `riser_kind` (section) to the schema.
   - Register the new scenes in `SCENES` and `vinyl` in `LEGIBLE_OBJECTS`.
   - Keep `retention_map.txt` semantics.
4. **Listen-check:** `bitloop music spec.json -o music.wav`.
   - The S5 "proof" must be audible: beats 26–30 have only lead_q + bass in unison, then at 30 the 16th lead comes back on top.
   - Lead vol may need −1 to −2 dB vs lead_q. Hand-polish the lead echo if 16ths smear.

## B. New scenes (draw in world units, ≥3 parallax layers come from `layers`)
### 1. `fractal_staff` (S1, S2, S5, S10): the hero of the video
- **Look:** a 5-line pixel staff (cream lines, 1 art px, spacing 6 world px) across the frame, with a small pixel treble clef at the left.
  - Note heads are 5×4 px ovals with 1 px stems.
  - Vertical position = series degree (1 degree = ½ staff space). Ledger lines where needed.
  - Notes scroll right→left at `rate` notes/beat. A fixed playhead column (turquoise glow) sits at x≈−20.
  - A note crossing the playhead lights turquoise (`Türkuaz Işık`, glow) on its exact 16th. The others are lapis/sis.
  - Tiny echo trails behind lit notes.
- **Params:**
  - `mode`: `play` | `nest` | `every4`
  - `rate` (4), `depth` (0–2), `playhead` (bool)
  - `zoom_into_note` (index of the note the camera crash-zooms into, S1)
  - `nest_preview` (from beat 4 the target note head shows a miniature staff inside it, with a pop)
  - `bass_staff` (a 2nd staff 40 px below showing the quarter-note copy)
  - `show_parent_edge` (S2: the enlarged rim of the parent note head frames the screen for the first 1.5 beats)
  - `dim_others`, `drop_to_bass_at` (every4 mode)
  - `converge_to_frame0`, `from_groove`
- **`every4` (S5, the TWIST):**
  - Every 4th note burns turquoise. The others fade to `Mürekkep` at 30 % (beat 0–2).
  - At `drop_to_bass_at`=2 the lit notes fall (outCubic, 0.75 beat, with a tiny pop SFX each) onto the bass staff, spaced 4× wider, forming **exactly the same contour** as the top melody.
  - Beats 4–8: the top 16th notes re-light at full brightness, and both staves light in sync on shared onsets (unison sparks).
- **`nest` + loop:**
  - Each note head can contain a scaled copy of the staff (scale factor F≈1/12, centred in the head). Recursion is drawn to `depth`.
  - **S10 must end on a frame identical to S1 frame 0:** same scroll phase (global beat 70 ≡ 0, wrap the series index at 280 → 0), camera zoom 1.0, pan 0, orbit phase 0.
  - The QC worker will diff the first/last frames.
  - `from_groove`: for the first 1.25 beats the staff lines appear as the vinyl's grooves straightening out (the portal transition carries it).

### 2. `koch` (S3)
- Koch snowflake, iteration increases by 1 on every beat: `iter_from` 0 → `iter_to` 4, `step_every` 1.
- Cobalt fill (dim ramp 0.35) and cream outline. New vertices spark turquoise for 0.25 beat with a `tick` SFX on each step (already event-driven if you emit sfx beats).
- Slow rotation via camera rot. `spark_notes`: 3–6 tiny note glyphs ride the perimeter. `inner_glow`: soft dithered glow at the centre.

### 3. `noise_scope` (S4)
- A CRT oscilloscope screen (rounded rect, Derin Lacivert, scanlines) with 3 stacked traces scrolling left:
  - **white** noise: coral, jagged
  - **pink 1/f**: turquoise. Generate it with the **Voss–McCartney algorithm**, a nice nod to Voss.
  - **brown** (integrated white): gök, slow drift
- Tiny 1-dot labels: `BEYAZ` / `1/F` / `KAHVE`.
- At `focus_at` (beat 3) the pink trace thickens and glows while the others dim to 40 %. A small coral `1975` tag appears on the scope bezel (`label_1975`).
- Seeded and deterministic. Traces must not jitter frame-to-frame beyond their scroll.
- **Terminal prop** (subtle tag) bottom-right types `> @hayret.piksel` then `> spektrum: 1/f`.

### 4. `series_tree` (S6)
- A binary tree of the infinity series. Root node "0" at the top grows one level per beat (`grow_every` 1) to `levels` 5 (32 leaves).
- Children of node n: 2n (left, value −a(n), coral tint) and 2n+1 (right, value a(n)+1, turquoise tint).
- Node = small note head with its value in 1-dot digits (signed). Edges are 1 px lines that draw in over 0.5 beat.
- `leaves_play`: the bottom row lights left→right on 16ths (same playhead logic).
- `show_rule`: the chalkboard prop (back layer, s 0.8 → subtle) shows `a(2n)=-a(n)` and `a(2n+1)=a(n)+1` in chalk. Add a `lines` param to `props.chalkboard`. The handle stays in the corner.

### 5. `shepard_stairs` (S7)
- A Penrose-style impossible staircase built from **piano keys**: white keys cream with lapis shading, black keys Gece. Square loop in isometric pixel perspective, 12 steps (`steps`).
- A glowing eighth-note sprite hops up one step every ½ beat (`climb_rate` 2). The staircase/camera rotates (`rot_per_beat`) so the sprite never actually gets higher. Make the hop SFX (tick) follow the Shepard steps.
- `ring_countdown_from` 4: a coral ring contracts around the sprite over beats 4–7.5, while turquoise glow grows.
- Beats 7.5–8: held breath, everything frozen except dust.

### 6. `mandel_zoom` (S8, the DROP)
- Escape-time Mandelbrot at art resolution (≈180×320, numpy-vectorised, float64), `max_iter` 96.
- `center` = seahorse valley (−0.743643887037151, 0.131825904205330). Zoom ×`zoom_per_beat` 1.6 per beat (×43 over 8 beats).
- Smooth-iteration bands mapped to Çini Gecesi ramps:
  - interior = Gece
  - far = Derin Lacivert → Kobalt → Lapis
  - near boundary = Firuze → Türkuaz Işık
  - rare coral sparkles on the outermost band
- 4×4 Bayer dither between bands. `band_on_beat`: palette-cycle the bands one step on every beat (chiptune "colour cycling").
- `note_emitters` 4: four streams of tiny note glyphs fly out of the boundary at 4 speeds (16th/8th/quarter/whole), the visual of "4 HIZ / 1 MELODİ".
- Frame 0 is the flash peak (`flash` transition). Shake/flash fire on the drop.

### 7. `object` kind `vinyl` (S9, the LEGIBLE TAG)
- Record disc radius ≈70 world px, Gece/Derin Lacivert with dithered concentric grooves.
- The groove is a **spiral of tiny note heads** (`groove: spiral_notes`) catching a turquoise specular highlight that sweeps with rotation. Full turn every `rpm_beats` 4.
- The pixel rotation is redrawn, not bitmap-rotated. The **label** does NOT rotate (or rotates but the text stays upright), to keep it legible.
- Centre label: cream disc r≈30 with the hayret eye mark on top and **`@hayret` / `.piksel`** in two lines in dark ink. Height ≥ 2 dots so it's phone-legible, contrast ≥ 7:1. `label_text` `SONSUZ / PLAK` in small coral.
- A tonearm enters from the top-right with a turquoise tip light pulsing on beats.
- `brand_at` 0.5 (with the sonic logo long note), `reveal` 1.5.
- **Register `vinyl` in `LEGIBLE_OBJECTS`.**

## C. Checks for the coder before handing to QC
- [ ] `validate spec.json` → OK. Only allowed warnings: none expected (the proxy is clean).
- [ ] Lit-note frames coincide with lead onsets (same formula). S5 lit notes = audible lead_q notes.
- [ ] S10 last frame ≈ S1 first frame. Audio loop seam clean (logo long note on beat 0).
- [ ] Captions ≤12 chars/line. The glyphs used incl. `= / . : ! ?` and İ Ş Ü Ö Ç Ğ already render (see storyboard.png).
- [ ] Tag count = 3 (terminal S4, chalkboard S6, vinyl S9). Not in the first 2 s.
