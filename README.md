# pixel-mimic: @hayret.piksel coded pixel-art science reels

Vertical (1080×1920, **30 fps**) pixel-art Reels/Shorts for the Turkish channel **@hayret.piksel**, made **entirely in code**: no
footage, no samples, no AI video. Every picture element, the chiptune soundtrack, every SFX and every narration letter
come from **one spec (JSON) on one beat clock**, so cuts, notes, SFX and text reveals are synced by construction.

The recipe started from an analysis of the reference Short
[Bit Wonder, "One Neuron of 86 Billion 🎧"](https://youtube.com/shorts/LXcZhstWlXM) using the
[ReelMimic](https://github.com/edenfunf/reelmimic) workflow. The structure is borrowed; the identity (palette, sonic logo,
diegetic tag, Turkish narration, per-topic music) is our own.

> **New agent? Read [`AGENTS.md`](AGENTS.md) first.** It holds the workflow, the role split and all of Kürşat's standing
> rules. Then read [`docs/WORKFLOW.md`](docs/WORKFLOW.md) (per-topic checklist) and [`docs/ENGINE.md`](docs/ENGINE.md).

## What a reel is made of
| Layer | Fixed or per video | Where |
|---|---|---|
| Brand: "Çini Gecesi" palette, hayret-eye logo (pupil = "!"), 4-note sonic logo, text style, diegetic `@hayret.piksel` tag | **fixed** | `brand/BRAND.md`, `bitloop/bitloop/spec.py` (`PRESETS["hayret"]`) |
| Music: tempo, meter, key, scale/makam, chip flavour, voices, drums, sections | **new for every topic** | `spec.music` |
| Edit: segments, scenes, layers, props, camera, transitions, narration, events | **new for every topic** | `spec.segments` |
| Palette | brand palette by default; a topic may add its own (per segment) | `spec.palette`, `segments[].palette` |

## Quick start
Requirements: Python 3.11+ (developed on 3.13), `ffmpeg` + `ffprobe` with libx264 and AAC on PATH.
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt            # engine + tests
pip install -r requirements-qc.txt         # optional: QC tools (librosa, pyloudnorm, opencv)

# tests (73, all must pass); each file also runs as a plain script
cd bitloop && for t in tests/test_*.py; do python "$t" || break; done; cd ..

# one project, end to end (example: evren-anlamak)
python projects/evren-anlamak/build_spec.py                      # build_spec.py -> spec.json + spec_proxy.json
B=bitloop/bitloop.sh; P=projects/evren-anlamak
$B validate $P/spec.json                                          # brand/quality rules + RETENTION MAP (0 errors required)
$B sheet    $P/spec.json -o $P/out/contact_sheet.png --every 1 --cols 10 --w 162   # contact sheet: look before rendering
$B strip    $P/spec.json --range 30:33 -o /tmp/strip.png          # frame strip around a moment
$B music    $P/spec.json -o /tmp/music.wav                        # soundtrack only, mastered to -14 LUFS: listen
$B render   $P/spec.json -o /tmp/preview.mp4 --draft              # 15 fps preview
tools/make_master.sh $P     # final: CRF 18 master + cover + CRF 4 intermediate -> two-pass upload encode -> out/upload.json
```
`bitloop.sh` uses `$BITLOOP_PY`, else `<repo>/.venv`, else `<repo>/venv`, else `python3`.
Rendering a 48 s reel takes several minutes on a multi-core box (frames render in parallel workers).

## Repo map
```
AGENTS.md                 onboarding for agents: workflow, roles, ALL standing rules, QC checklist, lessons learned
docs/WORKFLOW.md          step-by-step checklist per topic (researcher -> approval -> render coder -> QC -> delivery)
docs/ENGINE.md            engine module map + spec key fields (authoring guide: recipe/recipe.md §12)
bitloop/                  the engine (Python + numpy + ffmpeg). README.md = full reference. tests/ = 73 tests
  bitloop.sh              launcher: bitloop.sh init|list|validate|info|music|still|sheet|strip|render
recipe/                   recipe.md (§12 = authoring guide, Turkish), recipe.json (spec schema), RESEARCHER_GUIDE.md,
                          ozet_tr.md (Turkish summary), pixel-science-loop.md (reference recipe notes)
brand/                    BRAND.md (brand guide, Turkish), brand_board.png, sonic_identity.mp3, music_range_demo.mp3, src/
projects/<slug>/          one folder per reel (see below)
tools/                    encode_upload.sh (two-pass upload encode), make_master.sh, finalize_package.py, qc/ (QC measurements)
ref/                      reference analysis notes + contact sheet (no video, no frame dumps)
```
### The four reels so far
| slug | title | music | pacing | status |
|---|---|---|---|---|
| `fraktal-muzik` | Bu Melodinin İçinde Kendisi Saklı 🎧 (42 s) | G dorian, 100 BPM, NES 2A03; Nørgård infinity-series melody, Shepard riser | punchy (pre-feedback) | QC'd, not posted |
| `gelecek-secim` | Geleceğini Bilseydin, Yine Seçebilir miydin? 🎧 (40 s) | E harmonic minor, 120 BPM, FM; list-series "prophecy" melody + lookahead whisper | punchy (pre-feedback) | QC'd, not posted |
| `canli-gozu` | Aynı Dünya, 6 Farklı Göz: Hayvanlar Ne Görüyor? 👁️ (48.9 s) | D major, 108 BPM, Game Boy; bat-chirp drum `B`, per-creature vision palettes | calm + narration | QC'd, not posted |
| `evren-anlamak` | Evrenin Bütün Kurallarını Bilseydik Ne Olurdu? 🌌 (48 s) | F# dorian, 100 BPM, SID; Rule-30 melody, chaos-twin bells, topic palettes | calm + narration | QC'd v2, not posted |

Each `projects/<slug>/` holds: `plan_tr.md` (scene plan, Turkish), `sources.md`, `build_spec.py` (**edit this, not the JSON**),
`spec.json` (target), `spec_proxy.json` (same timeline on older scenes, used while new scenes are being coded),
`render_brief.md` (what the render coder had to build), `retention_map.txt` (validator output), `qc_report.md`,
`storyboard.png`, optional `palette_board.png` / `palettes.py` / `visions.py`, and `out/{upload.json, cover.png, contact_sheet.png}`.
**Videos are not in git** (`*.mp4` ignored); rebuild them with `tools/make_master.sh projects/<slug>`.
Storyboard/contact-sheet PNGs were palette-quantised (256 colours) to keep the repo small.

## Türkçe özet
Bu repo, @hayret.piksel kanalı için **tamamen kodla** üretilen piksel-art bilim Reels'lerinin motorunu (`bitloop`), tarifini
(`recipe/`), marka kılavuzunu (`brand/`) ve şimdiye kadarki dört videonun kaynak dosyalarını içerir. Görüntü, chiptune müzik,
efektler ve anlatım yazıları tek bir vuruş saatinden üretildiği için her şey kendiliğinden senkron. Ekrandaki bütün yazılar
**Türkçe** ve motorun kendi 5×7 piksel fontuyla yazılır. Hiçbir video kullanıcı onayı olmadan paylaşılmaz.
İlk kez gelen bir agent önce `AGENTS.md` dosyasını okumalı.
