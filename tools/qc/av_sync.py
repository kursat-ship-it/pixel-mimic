"""A/V sync check: cross-correlates visual change (frame diff) with the audio onset envelope, per frame.
Usage: python tools/qc/av_sync.py out/<slug>.mp4 [--spec spec.json]
Best lag must be 0 frames (± = video late/early). Whole-film r is often weak (0.05–0.3) because calm scenes move
continuously; that alone is not a failure — check the lag, and with --spec the per-segment-cut alignment."""
import argparse
import numpy as np
from _common import frames_small, audio, segment_bounds, FPS

ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--spec"); a = ap.parse_args()
F = frames_small(a.video).astype(np.float32)
d = np.abs(np.diff(F, axis=0)).mean((1, 2, 3))            # d[i]: change from frame i to i+1 → event at frame i+1
y, sr = audio(a.video); m = y.mean(1)
try:
    import librosa
    env = librosa.onset.onset_strength(y=m, sr=sr, hop_length=160); t_env = np.arange(len(env)) * 160 / sr
except ImportError:                                        # crude fallback: positive RMS flux
    hop = 160; r = np.sqrt(np.convolve(m ** 2, np.ones(hop) / hop, "same")[::hop]); env = np.maximum(np.diff(r, prepend=r[0]), 0)
    t_env = np.arange(len(env)) * hop / sr
aud = np.array([env[(t_env >= k / FPS - 1 / 60) & (t_env < k / FPS + 1 / 60)].max(initial=0) for k in range(1, len(d) + 1)])
v = d - np.median(d); au = aud - np.median(aud)
res = []
for lag in range(-6, 7):
    c = np.corrcoef(v[lag:], au[:len(au) - lag])[0, 1] if lag >= 0 else np.corrcoef(v[:lag], au[-lag:])[0, 1]
    res.append((round(float(c), 3), lag))
best = max(res)
print("xcorr by lag (frames, + = video later):", sorted(res, key=lambda x: x[1]))
print(f"BEST lag {best[1]} frames (r {best[0]})   [must be 0 when r is meaningful (>~0.1); a weak r means the picture moves\n  continuously (calm pacing) — then judge sync from the cut table below + `bitloop strip` around hits]")
if a.spec:
    segs, _ = segment_bounds(a.spec)
    print("\ncut      t_s    video_peak_off_ms")
    for sid, t0, _ in segs[1:]:
        j = int(round(t0 * FPS)); lo = max(0, j - 4); w = d[lo:j + 4]
        print(f"{sid:6} {t0:7.2f} {round(((lo + int(np.argmax(w)) + 1) / FPS - t0) * 1000):6d}")
