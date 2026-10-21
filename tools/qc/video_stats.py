"""Visual QC numbers for a rendered reel.
Usage: python tools/qc/video_stats.py out/<slug>.mp4 [--spec spec.json]
Prints: frame count, median/per-second luminance, darkest frames + any near-black frames (lum < 12/255: black frames in
transitions were a real bug), per-second motion, longest near-static run (calm pacing: no dead spot > 2 s), loop-seam
difference (last frame vs first frame, should be ≈ the median frame-to-frame diff), and per-segment motion with --spec."""
import argparse
import numpy as np
from _common import frames_small, segment_bounds, FPS

ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--spec"); ap.add_argument("--static", type=float, default=0.4)
a = ap.parse_args()
F = frames_small(a.video).astype(np.float32)
lum = (F @ np.array([.2126, .7152, .0722], np.float32)).mean((1, 2))
d = np.abs(np.diff(F, axis=0)).mean((1, 2, 3))
n = len(F)
print(f"frames {n} ({n / FPS:.3f} s @ {FPS} fps)   median lum {np.median(lum):.1f}/255")
dark = np.argsort(lum)[:8]
print("darkest:", [(round(float(i) / FPS, 2), round(float(lum[i]), 1)) for i in sorted(dark)])
black = np.nonzero(lum < 12)[0]
print("near-black frames (lum<12):", [round(float(i) / FPS, 2) for i in black] or "none")
print("per-second lum:", [int(lum[i * FPS:(i + 1) * FPS].mean()) for i in range((n + FPS - 1) // FPS)])
print("per-second motion:", [round(float(d[i * FPS:(i + 1) * FPS].mean()), 1) for i in range((len(d) + FPS - 1) // FPS)])
run = best = end = 0
for i, x in enumerate(d < a.static):
    run = run + 1 if x else 0
    if run > best: best, end = run, i
print(f"longest near-static run {best} frames ({best / FPS:.2f} s) ending {end / FPS:.2f} s   [rule: < 2 s dead spot]")
seam = float(np.abs(F[-1] - F[0]).mean())
print(f"loop seam diff {seam:.2f}   median frame diff {np.median(d):.2f}   [seam should be ~ median]")
if a.spec:
    segs, dur = segment_bounds(a.spec)
    print("\nsegment  start    end   motion  lum")
    for sid, t0, t1 in segs:
        i0, i1 = int(t0 * FPS), max(int(t0 * FPS) + 1, int(t1 * FPS))
        print(f"{sid:6} {t0:6.2f} {t1:6.2f} {d[i0:i1 - 1].mean() if i1 - 1 > i0 else 0:7.2f} {lum[i0:i1].mean():5.1f}")
