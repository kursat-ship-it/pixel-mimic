"""Shared helpers for the QC scripts (run them from anywhere; the repo's bitloop package is put on sys.path)."""
import os, subprocess, sys
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "bitloop"))
FPS = 30


def frames_small(video, w=135, h=240):
    """All frames, area-downscaled to w×h RGB (default 1/8 of 1080×1920) → uint8 array [n, h, w, 3]."""
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"scale={w}:{h}:flags=area", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w, 3)


def audio(path, sr=48000):
    """Decode any audio/video file to float32 stereo [n, 2] at sr via ffmpeg."""
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2), sr


def segment_bounds(spec_path):
    """[(id, start_s, end_s)] from the engine's own tempo map, so QC tables line up with the spec exactly."""
    from bitloop import spec as S
    s = S.load(spec_path)
    return [(g["id"], float(g["start_s"]), float(g["end_s"])) for g in s["segments"]], float(s["duration_s"])
