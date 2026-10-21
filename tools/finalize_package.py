"""Write the delivery metadata for a project: out/upload.json (relative paths, posted: false) + out/cover.png.
`bitloop render --package` writes <out>.cover.png (at meta.cover_t) and <out>.upload.json with an absolute path; this
normalises them into the layout every project uses. It NEVER posts anything — `posted` stays false until the user
approves and posts by hand.
Usage: python tools/finalize_package.py projects/<slug> [--note "v2 after QC ..."]"""
import argparse, json, os, shutil, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bitloop"))
from bitloop import spec as S
from bitloop.cli import cover_t

ap = argparse.ArgumentParser(); ap.add_argument("project"); ap.add_argument("--note", default=""); a = ap.parse_args()
P = os.path.abspath(a.project); slug = os.path.basename(P); out = os.path.join(P, "out")
s = S.load(os.path.join(P, "spec.json")); m = s["meta"]
pk = os.path.join(out, f"{slug}_master.cover.png")
if os.path.exists(pk): shutil.copyfile(pk, os.path.join(out, "cover.png"))
up = {"title": m.get("title", ""), "description": m.get("description", ""), "hashtags": m.get("hashtags", []),
      "duration_s": round(s["duration_s"], 2), "file": f"out/{slug}.mp4", "master": f"out/{slug}_master.mp4",
      "cover": "out/cover.png", "cover_t": cover_t(s), "resolution": "1080x1920", "fps": 30, "loop": bool(s.get("loop")),
      "posted": False, "sources": "sources.md", "note": a.note or "Nothing posted."}
json.dump(up, open(os.path.join(out, "upload.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(os.path.join(out, "upload.json"), "| cover_t", up["cover_t"], "| posted: false")
