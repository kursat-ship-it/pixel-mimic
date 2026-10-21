"""bitloop CLI.

  python -m bitloop init   <dir> [--archetype NAME]    new topic folder with spec.json (blank or an archetype skeleton)
  python -m bitloop validate <spec.json>               brand + quality + retention rules, prints the RETENTION MAP
  python -m bitloop list   archetypes|styles|scales|drums|transitions|props|scenes
  python -m bitloop info   <spec.json>               timeline table (beats ↔ seconds)
  python -m bitloop music  <spec.json> -o music.wav    soundtrack only (synth or file + SFX), mastered to -14 LUFS
  python -m bitloop still  <spec.json> -t 1.5 -o f.png one full-res frame
  python -m bitloop sheet  <spec.json> -o sheet.jpg [--every 1 | --times 0,3.5,…]
  python -m bitloop strip  <spec.json> --range 20:24 [--fps 12] -o strip.jpg
  python -m bitloop render <spec.json> -o out.mp4 [--draft] [--fps N] [--range a:b] [--workers N] [--no-audio] [--package]
"""
import argparse, json, os, shutil, sys
from . import spec as S

HERE = os.path.dirname(__file__)


def _load(p, strict=True):
    s = S.load(p)
    errs, warns = S.validate(s)
    for w in warns: print("  warn:", w)
    if errs:
        for e in errs: print("  ERROR:", e)
        if strict: sys.exit(2)
    return s


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bitloop", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("init"); a.add_argument("dir"); a.add_argument("--force", action="store_true")
    a.add_argument("--archetype", default="blank")
    a = sub.add_parser("list"); a.add_argument("what", choices=["archetypes", "styles", "scales", "drums", "transitions", "props", "scenes"])
    for name in ("validate", "info"):
        a = sub.add_parser(name); a.add_argument("spec")
    a = sub.add_parser("music"); a.add_argument("spec"); a.add_argument("-o", "--out", required=True)
    a = sub.add_parser("still"); a.add_argument("spec"); a.add_argument("-t", type=float, default=0); a.add_argument("-o", "--out", required=True)
    a = sub.add_parser("sheet"); a.add_argument("spec"); a.add_argument("-o", "--out", required=True)
    a.add_argument("--every", type=float, default=1.0); a.add_argument("--times"); a.add_argument("--cols", type=int, default=8); a.add_argument("--w", type=int, default=216)
    a = sub.add_parser("strip"); a.add_argument("spec"); a.add_argument("--range", required=True); a.add_argument("--fps", type=float, default=12)
    a.add_argument("-o", "--out", required=True); a.add_argument("--w", type=int, default=216)
    a = sub.add_parser("render"); a.add_argument("spec"); a.add_argument("-o", "--out", required=True)
    a.add_argument("--fps", type=int); a.add_argument("--range"); a.add_argument("--workers", type=int)
    a.add_argument("--draft", action="store_true", help="15 fps, fast preset (preview quality)")
    a.add_argument("--no-audio", action="store_true"); a.add_argument("--crf", type=int, default=18)
    a.add_argument("--package", action="store_true", help="also write cover.png + upload.json (title/description) next to the mp4")
    a = ap.parse_args(argv)

    if a.cmd == "init":
        from .archetypes import make
        os.makedirs(a.dir, exist_ok=True); dst = os.path.join(a.dir, "spec.json")
        if os.path.exists(dst) and not a.force: sys.exit(f"{dst} exists (use --force)")
        if a.archetype == "blank":
            spec = json.load(open(os.path.join(HERE, "templates", "blank.json"), encoding="utf-8"))
        elif a.archetype == "reference":
            spec = json.load(open(os.path.join(HERE, "templates", "reference_scale_journey.json"), encoding="utf-8"))
        else: spec = make(a.archetype)
        json.dump(spec, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"wrote {dst} ({a.archetype}) — design music + edit for the topic, fill every {{{{slot}}}}, then: bitloop validate {dst}")
    elif a.cmd == "list":
        _list(a.what)
    elif a.cmd == "validate":
        s = S.load(a.spec); errs, warns = S.validate(s)
        print(S.table(s)); print(); print(S.retention_map(s)[0]); print()
        for w in warns: print("warn:", w)
        for e in errs: print("ERROR:", e)
        print("OK" if not errs else f"{len(errs)} error(s)"); sys.exit(1 if errs else 0)
    elif a.cmd == "info":
        print(S.table(S.load(a.spec)))
    elif a.cmd == "music":
        from .music import build_audio
        s = _load(a.spec); print(build_audio(s, a.out))
    elif a.cmd == "still":
        from .render import still
        still(_load(a.spec, False), a.t, a.out); print(a.out)
    elif a.cmd == "sheet":
        from .render import sheet
        s = _load(a.spec, False)
        ts = [float(x) for x in a.times.split(",")] if a.times else [k * a.every for k in range(int(s["duration_s"] / a.every) + 1)]
        ts = [min(t, s["duration_s"] - 1e-3) for t in ts]
        print(sheet(s, ts, a.out, cols=a.cols, w=a.w))
    elif a.cmd == "strip":
        from .render import sheet
        s = _load(a.spec, False); t0, t1 = map(float, a.range.split(":"))
        n = int((t1 - t0) * a.fps); print(sheet(s, [t0 + k / a.fps for k in range(n)], a.out, cols=min(12, n), w=a.w))
    elif a.cmd == "render":
        from .render import render, still
        s = _load(a.spec)
        fps = a.fps or (15 if a.draft else None)
        t0, t1 = (map(float, a.range.split(":")) if a.range else (0.0, None))
        render(s, a.out, fps=fps, t0=t0, t1=t1, workers=a.workers, crf=(23 if a.draft else a.crf),
               preset=("veryfast" if a.draft else "medium"), audio=not a.no_audio)
        if a.package:
            base = os.path.splitext(a.out)[0]
            still(s, cover_t(s), base + ".cover.png")
            m = s["meta"]
            json.dump({"title": m.get("title", ""), "description": m.get("description", ""), "hashtags": m.get("hashtags", []),
                       "duration_s": round(s["duration_s"], 2), "file": os.path.abspath(a.out)},
                      open(base + ".upload.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("package:", base + ".cover.png", base + ".upload.json")


def cover_t(s):
    """cover time: meta.cover_t (where the planner writes it), legacy top-level cover_t, else 1.0 s; clamped into the film"""
    t = (s.get("meta") or {}).get("cover_t", s.get("cover_t", 1.0))
    return float(min(max(0.0, float(t)), s.get("duration_s", 1e9) - 1e-3))


def _list(what):
    if what == "archetypes":
        from .archetypes import ARCHETYPES
        for k, f in ARCHETYPES.items(): print(f"{k:22} {f.__doc__.strip()}")
        print(f"{'blank':22} minimal free spec;  reference = the analysed reference video as a spec")
    elif what == "styles":
        from .music import STYLES
        for k, v in STYLES.items(): print(f"{k:20} {v['bpm']:>6} BPM {v['meter']:5} {v['key']:2} {v['scale']:18} {v['flavour']:8} drums={v['drums']}")
    elif what == "scales":
        from .theory import SCALES
        for k, (semi, cents, d) in SCALES.items(): print(f"{k:18} {semi}{'  ~' + str(cents) + ' c' if cents else ''}  {d}")
    elif what == "drums":
        from .drums import PATTERNS
        for k, v in PATTERNS.items(): print(f"{k:14} {v.get('meter', 'any'):5} " + "  ".join(f"{i}:{g}" for i, g in v.items() if i not in ('meter', 'swing')))
        print("auto           any   generated from the meter grouping (aksak accents)")
    elif what == "transitions":
        from .transitions import TRANSITIONS
        for k, v in TRANSITIONS.items(): print(f"{k:11} {v['beats']:>4} b  {v['align']:6}  sfx={str(v['sfx']):9} {v['desc']}")
    elif what == "props":
        from .props import PROPS
        print(", ".join(PROPS))
    elif what == "scenes":
        from .scenes import SCENES
        print(", ".join(SCENES))


if __name__ == "__main__":
    main()
