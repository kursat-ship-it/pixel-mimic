# QC report: fraktal-muzik (independent QC, 2026-10-20)

Final: out/fraktal-muzik.mp4 (upload encode, 24.0 MB, 1080×1920, 30 fps, H.264 High 4.2 2-pass 4.4 Mbit/s, AAC 192k, faststart)
Master: out/fraktal-muzik_master.mp4 (CRF 18, 65.7 MB). Previous: out/fraktal-muzik_v1.mp4.
Upload encode vs near-lossless render: SSIM 0.945 overall; lowest is 0.83 on the 0.3 s drop flash at 28.8 s.
Audio: −14.2 LUFS, −1.6 dBTP, LRA 4.8. A/V cross-correlation peaks at 0 frames.

## Engine changes (bitloop)
- bitmap.py: `snap=True` option (draw_bitmap / draw_text / draw_mark / minifont.draw_mini). It stamps each dot as exactly k×k pixels on the art grid, for upright text below 1.75 px/dot.
- scenes.py (vinyl):
  - Handle, eye mark and small print are drawn snapped.
  - Removed the spindle dot that turned ".piksel" into ".pikse]".
  - The label is matte: the glow buffer is cleared under it, so "SONSUZ PLAK" no longer dithers away.
- minifont.py: the P glyph has a rounded bowl (it used to read as "ºLAK").
- render.py + transitions.py (portal):
  - The outgoing scene now dives with a live camera instead of a nearest-neighbour bitmap blow-up.
  - The incoming frame is no longer shrunk, so the black border around it at 38.6 s is gone.
- transitions.py (flash): peak capped at 0.88 (`peak` param), so no frame is a flat featureless cream card.
- scenes_math.py (mandel_zoom): `adapt_bands` measures escape depth from each frame's own low percentile. Late S8 is no longer a flat türkuaz wall.
- scenes_music.py (fractal_staff): `keys` adds a pixel piano under the staff, which fills the empty lower third.
  - The lead note's key lights türkuaz on its exact onset.
  - A mercan pip marks the 4× slower copy.
  - It is a pure function of the global beat, so the loop seam stays safe.
- music.py: master high-shelf at 7 kHz, −3 dB (`music.hf_shelf_db`). Energy at 12–24 kHz is down from −17 to −24 dB relative to the full band; LUFS target unchanged.
- tests/test_fractal.py: +1 regression test (snapped text exact, portal without a black border). 14 + 12 tests pass; validate OK with 0 warnings.

## Project changes (build_spec.py)
- S1 and S10: `"keys": true`.
- meta.description rewritten:
  - "ses" changed to "gürlük".
  - "müziğin tamamı" changed to "melodi ve bas", because the drums, Shepard riser and SFX are not from the series.
  - Added the inversion fact and a comment prompt.
- Hashtags: #bilim replaced by #matematik (validator allows 3–6).

## Upload encode command
two-pass libx264 -preset slow -b:v 4400k -maxrate 9000k -bufsize 9000k -tune animation
-x264-params no-deblock=1:psy-rd=0.6,0:aq-mode=2 -g 60 -pix_fmt yuv420p -profile:v high -level 4.2 bt709, audio copied from master, +faststart
(source: render --crf 4 near-lossless intermediate)
