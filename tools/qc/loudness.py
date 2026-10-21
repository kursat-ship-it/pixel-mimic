"""Audio QC: integrated loudness (target -14 LUFS), true peak (≤ -1 dBTP, measured after AAC), LRA, spectral balance,
per-segment loudness/crest and a phone-speaker simulation (300 Hz high-pass) per segment.
Usage: python tools/qc/loudness.py out/<slug>.mp4|music.wav [--spec spec.json]
Needs pyloudnorm (requirements-qc.txt); true peak/LRA come from ffmpeg ebur128."""
import argparse, re, subprocess
import numpy as np
from _common import audio, segment_bounds

ap = argparse.ArgumentParser(); ap.add_argument("media"); ap.add_argument("--spec"); a = ap.parse_args()
r = subprocess.run(["ffmpeg", "-nostats", "-i", a.media, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                   capture_output=True, text=True).stderr.split("Summary:")[-1]
g = lambda k: (re.search(k + r":\s+(-?[\d.]+)", r) or [None, "nan"])[1]
print(f"ebur128: I {g('I')} LUFS   LRA {g('LRA')} LU   true peak {g('Peak')} dBFS   [targets: -14 ±0.5, TP ≤ -1]")
y, sr = audio(a.media); m = y.mean(1)
from scipy.signal import welch, butter, sosfilt
f, P = welch(m, sr, nperseg=8192); tot = P.sum()
print("bands dB re total:", {f"{lo}-{hi}": round(float(10 * np.log10(P[(f >= lo) & (f < hi)].sum() / tot + 1e-12)), 1)
                             for lo, hi in [(20, 120), (120, 300), (300, 500), (500, 2000), (2000, 6000), (6000, 12000), (12000, 22000)]})
try:
    import pyloudnorm as pyln
except ImportError:
    raise SystemExit("pip install pyloudnorm for per-segment + phone numbers")
meter = pyln.Meter(sr); hp = sosfilt(butter(4, 300, "hp", fs=sr, output="sos"), y, axis=0)
L = lambda x: meter.integrated_loudness(x) if len(x) > sr * .5 else float("nan")
print(f"pyloudnorm I {L(y):.1f}   phone-sim (300 Hz HP) I {L(hp):.1f}   [phone loss > ~5 LU = mix too bass-heavy]")
if a.spec:
    segs, _ = segment_bounds(a.spec)
    print("\nsegment  LUFS  phone  loss  crest_dB")
    for sid, t0, t1 in segs:
        s = slice(int(t0 * sr), int(t1 * sr)); x = y[s]
        crest = 20 * np.log10(np.abs(x).max() + 1e-9) - 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
        lf, lp = L(x), L(hp[s]); print(f"{sid:6} {lf:6.1f} {lp:6.1f} {lp - lf:5.1f} {crest:6.1f}")
