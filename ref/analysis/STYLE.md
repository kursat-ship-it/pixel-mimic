2d-pixel（外觀是帶「偽 3D」明暗的像素藝術：球體/膠囊有柔和陰影與高光，再量化到 6px 像素格 + 抖色；不是 live-action，也不是 AI 實拍）

# STYLE — "One Neuron of 86 Billion 🎧" (Bit Wonder, @bitwonder) · 48.0 s · 1080×1920 · 60 fps

## Medium / look
- Pixel art at **180×320 art pixels, ×6 nearest-neighbour → 1080×1920** (measured: dominant column period = 6 px).
  Shapes are shaded like soft 3D (spheres, capsules, glows) then quantised + Bayer-dithered; bloom/glow is dithered too.
- Palette (whole film, very consistent): near-black violet bg `#11071A` / `#221031`, mid violet `#663B9F`/`#6E3FAC`,
  lilac highlight `#B087DC`, off-white `#F4ECEB`, single warm accent amber/orange `#E5AF4D` / `#AB603A` (the "energy").
  Colour arc: cool violet everywhere; amber = signal/energy, grows from a dot (0 s) → floods (6 s) → whole brain glows gold (35–44 s).
- No characters. Subjects are objects/systems (neuron, membrane, axon, synapse, network, brain, light bulb).
- Mean brightness 0.19 (dark, low-key, glow-on-black); vignette; floating dust particles in every shot.

## Shot list (hard cuts only at 3.52, 16.0, 24.0 s; everything else is one continuous camera that pushes/pulls/morphs)
| # | time (s) | dur s / beats | content | camera & pace | transition in |
|---|---|---|---|---|---|
| B1 | 0.00–3.52 | 3.5 / 6.9 | Neuron soma, spark at axon hillock, orange oscilloscope spike trace at bottom; caption "ONE NEURON / FIRES / HOW FAR?" | slow push-in + slight orbit, ends in **crash-zoom into the spark** | loop-in from B10 (same frame) |
| B2 | 3.52–7.30 | 3.8 / 7.4 | Macro of membrane (ion channels as violet spheres); orange ions flood through; "SODIUM / RUSHES IN" | slow pull-out | hard cut on beat (match on scale: spark → macro) |
| B3 | 7.30–12.0 | 4.7 / 9.2 | Side view axon, myelin capsules, spark hops node to node; "IT HOPS / OVER MYELIN" | continuous pull-out, static framing | continuous (morph by camera) |
| B4 | 12.0–16.0 | 4.0 / 7.8 | Camera tilts to steep perspective: several axons, sparks racing; "FASTEST / NERVES / **100+ M/S**" | tilt/roll into diagonal perspective, then track along axon to terminal | continuous tilt |
| B5 | 16.0–20.0 | 4.0 / 7.8 | Synaptic terminal close-up full of vesicles, amber rim; "A GAP: / THE SYNAPSE" | slow push | hard cut on beat |
| B6 | 20.0–24.0 | 4.0 / 7.8 | Vesicles release dots across gap; pull back to dendrite of next neuron whose soma glows & ring tightens (summation); "CHEMICALS / CROSS IT" (20.6–22.5) then **wordless build** | slow pull-out, then hold while glow grows | continuous |
| B7 | 24.0–30.5 | 6.5 / 12.7 | **HIT**: next neuron fires — white-gold flare + shockwave ring; pull out to network, waves of sparks light up many neurons; no caption | fast pull-out → slow drift | hard cut on downbeat |
| B8 | 30.5–35.2 | 4.7 / 9.2 | Network resolves into a particle **brain** silhouette, gold waves sweep across; "ONE OF / **86 BILLION** / NEURONS" | pull-out/morph | continuous morph |
| B9 | 35.2–44.6 | 9.4 / 18.4 | Glass **light bulb** materialises around the brain (filament = brain); "ALL OF IT / RUNS ON / **~20 WATTS**"; brand tag "@BITWONDER / 20W" etched on glass (≈40.1–44.3) | pull-out reveal then near-static hold | continuous reveal |
| B10 | 44.6–48.0 | 3.4 / 6.7 | Push into bulb → through brain → into network → lands back on B1 frame; first caption fades back in (47.1 s) | **fast push-in (fastest move in the film)** | continuous → seamless loop to 0 s |

Counts: 3 hard cuts → 4 "shots" by detector (analyze.py with crop reported 6, a crop artefact); **10 visual beats**, mean beat length **4.8 s ≈ 9.4 musical beats** (core chain beats B2–B6 are exactly ~8 beats = 2 bars each).

## Editing / rhythm
- Music 117.45 BPM (beat 0.511 s), first beat 1.533 s. Hard cuts land within ±70 ms of a beat (3.52, 16.0, 24.0).
- Caption grid: captions start every **4.0 s (≈8 beats)**: 0.0, 4.6, 8.6, 12.6, 16.6, 20.6 → then a wordless gap 22.5–32.25 s (build + hit + reveal) → 32.25, 36.35. Each caption ≈2.3 s on (≈4.5 beats), 1.7 s off.
- Sound-synced visuals: spark/flash brightness rises correlate with audio onsets at lag 0 (r≈0.31 vs ~0 at other lags) → every spark hop / flash is placed on a note ("every neuron playing the beat").
- Transitions: no fades to black, no wipes. Only (a) crash-zoom-through into a bright point then hard cut to macro, (b) continuous camera morph (pull-out reveals new context; network → brain → bulb), (c) push-through back to start (loop).

## Typography
- Font: chunky monospace pixel font, ALL CAPS, glyph stroke 12 px (= 2 art px), line height 120 px, cap height ≈80 px.
- Box: solid near-black `#05000C` rectangle hugging the text (≈24 px padding), top edge at y=186 px (≈10 % from top), horizontally centred; 1–3 lines, ≤12 chars/line, ≤6 words.
- Colours: text `#F0E8F0`; the **number/key fact** line in amber `#F8D070` ("100+ M/S", "86 BILLION", "~20 WATTS").
- Animation: ~0.1 s dithered fade-in (ghost text first, then box), static, ~0.1 s dithered fade-out. No typewriter, no bounce.
- In-world text: brand handle etched on the glass of the final object, same pixel font, thin.

## Sound
- No voice-over (Whisper found no speech). Music-only (title 🎧 = "sound on"). Bass-heavy, steady electronic/lo-fi pulse, centroid ≈2.1 kHz, ≈4.1 onsets/s (8th notes), loudness flat ≈−13 dB with small dips before 9.5 s, 17 s, 38 s. Inferred key around D minor (chroma D, A, C, B♭) — inferred, not verified by ear.

## Narrative
- Formula: **"follow ONE tiny thing through a chain of scale → reveal it is one of N → collapse it into one everyday metaphor with a number → loop back."**
- Hook (0–3.5 s): subject + question in caption ("ONE NEURON FIRES — HOW FAR?"), the action already happening, spike trace as data cue.
- 5 mechanism steps, one fact each, 2–4 word captions, each step = 2 bars.
- Climax: the chain closes (next neuron fires) → zoom-out to the system.
- Payoff: big-number fact (86 BILLION) + relatable metaphor (bulb, ~20 W). Brand tag sits inside the metaphor object.
- Ending/CTA: no spoken/explicit CTA; the loop (end frame == first frame, first caption returns) IS the retention CTA.
