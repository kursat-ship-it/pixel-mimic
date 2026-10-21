# WORKFLOW: one topic, start to finish

Checklist for each new topic. Roles and rules are in [`../AGENTS.md`](../AGENTS.md); the authoring guide is
[`../recipe/recipe.md`](../recipe/recipe.md) §12 and the planner guide [`../recipe/RESEARCHER_GUIDE.md`](../recipe/RESEARCHER_GUIDE.md).
Paths are relative to the repo root; `B=bitloop/bitloop.sh`, `P=projects/<slug>` (slug = short Turkish kebab-case, e.g. `evren-anlamak`).

## 0. Intake (orchestrator)
- [ ] Topic from Kürşat (Turkish). Note any new feedback; it becomes a standing rule in `AGENTS.md` §1.
- [ ] Create the folder: `$B init $P --archetype <name|blank>` (`$B list archetypes`) or copy the shape of an earlier `build_spec.py`.
- [ ] Spawn the researcher/editor agent with: the topic, `AGENTS.md`, `recipe/recipe.md` §12, `recipe/RESEARCHER_GUIDE.md`, `brand/BRAND.md`,
      and the previous reels' `plan_tr.md` (so music/edit are **different** this time).

## 1. Research + edit design (researcher/editor)
- [ ] **Sources first** → `sources.md`: each fact with a citation + URL + access date, where it is used (S#), and whether
      it is a verbatim quote or a paraphrase. Note contested points and how they are softened.
- [ ] **Honest answer + "hayret" moment**: what is surprising, what is the twist, what is the payoff.
- [ ] **Music design for this topic** (different from earlier reels): bpm/tempo map, meter, key, scale/makam, flavour,
      voices, drums, sections (build / stop / drop / riser / level_db), how the music *demonstrates* the idea,
      sonic logo at reveal + loop.
- [ ] **Edit**: 8–11 segments (~3–5 s each, calm), roles hook → … → twist (30–80 %) → reveal/payoff (last 45 %) → loop;
      scene + ≥ 3 layers + camera (small, slow) + transition (≥ 3 types, fast ones ≤ ~1 per 10 s) + events.
- [ ] **Narration** in Turkish full sentences per segment: place, size, reveal, rate, word count and reading time
      (0.6 + 0.35 × words) in the plan table; hook ≤ ~12 words, readable by ~3 s; nothing in the bottom 18 %.
- [ ] **Tag**: where `@hayret.piksel` lives in the world (1 legible at the reveal, 1–2 subtle), not in the first 2 s.
- [ ] **Palette**: brand, or topic palette(s) per segment (+ `palette_board.png`), keeping `#04060E` / `#F4ECDC`.
- [ ] **Titles** (2–3 options, ≤ 60 chars), description (fact + nuance + 👇), 3–6 hashtags incl. `#hayretpiksel`, `meta.cover_t`.
- [ ] Write `plan_tr.md` (table format in RESEARCHER_GUIDE §5) and `build_spec.py` → `python $P/build_spec.py`.
- [ ] `$B validate $P/spec_proxy.json > $P/retention_map.txt` (proxy = same timeline on existing scenes) and the target
      `spec.json` (errors only for not-yet-built scenes). 0 warnings left except intended ones (duration).
- [ ] `storyboard.png` (`$B sheet` of the proxy, or engine stills) and `render_brief.md`: every new scene/param the coder must
      build, with exact behaviour, frame-0 requirements, loop-seam requirements and what is already supported.

## 2. Approval (orchestrator → Kürşat, in Turkish)
- [ ] Show the scene plan (short table), retention map highlights, music idea, title options, length; list open choices with a default.
- [ ] **Wait for approval** (or apply his changes) before the expensive render.

## 3. Render (render coder)
- [ ] Back up `bitloop/` outside the repo before engine work (e.g. `/tmp/bitloop_bak_<slug>`).
- [ ] Implement new scenes/params per `render_brief.md`. **New params default to old behaviour; add tests**; run all tests.
- [ ] `$B validate $P/spec.json` → 0 errors. Update `retention_map.txt`.
- [ ] Look before you render: `$B sheet $P/spec.json -o /tmp/sheet.png`, `$B strip … --range a:b` around cuts, `$B still -t <cover_t>`.
- [ ] `$B music $P/spec.json -o /tmp/m.wav` and listen.
- [ ] Draft: `$B render $P/spec.json -o /tmp/<slug>_draft.mp4 --draft`.
- [ ] Final: `tools/make_master.sh $P` (master CRF 18 + `--package` cover, CRF 4 intermediate, two-pass upload, `upload.json`).
- [ ] `$B sheet $P/spec.json -o $P/out/contact_sheet.png --every 1 --cols 10 --w 162`.
- [ ] Hand over a list of **known issues** for QC (be honest: unchecked audio, busy frames, etc.).

## 4. Independent QC (a fresh agent)
- [ ] Copy the current upload to `out/<slug>_v1.mp4` (and back up `build_spec.py`, `spec.json`, `upload.json`, cover, sheet outside the repo).
- [ ] Run the measurements (§5), watch the film at phone size, read every sentence, check every fact against `sources.md`.
- [ ] Check that Kürşat's feedback is applied (narrator text, reading time, placements, calm motion, palette quality).
- [ ] **Fix what you find** (spec via `build_spec.py`, engine via new default-off params + tests), re-render, re-measure.
- [ ] Write `qc_report.md` (Turkish): scores v1 → v2 for Görsel / Retention / Ses / Bilgi doğruluğu / Teslim / Metadata,
      feedback check, numbered findings + fixes, remaining issues, verification numbers, files, verdict.
- [ ] `python tools/finalize_package.py $P --note "v2 after QC …"` → `posted: false`.

## 5. QC measurement commands
```bash
V=$P/out/<slug>.mp4
tools/qc/integrity.sh $V                                  # frames, durations, decode errors, bt709, faststart, size
python tools/qc/video_stats.py $V --spec $P/spec.json     # lum, near-black frames, motion, static runs, loop seam, per segment
python tools/qc/av_sync.py $V --spec $P/spec.json         # A/V xcorr lag (must be 0) + cut alignment table
python tools/qc/loudness.py $V --spec $P/spec.json        # LUFS / TP / LRA, bands, per-segment + phone-speaker simulation
python tools/qc/stems.py $P/spec.json /tmp/stem --keep lead,whisper   # is that voice audible? (same-stem comparison)
tools/qc/ssim.sh $V /tmp/<slug>_crf4.mp4                  # upload vs near-lossless intermediate
$B strip $P/spec.json --range 21:23 --fps 30 -o /tmp/s.png   # frame-exact look at a hit/cut
```
Targets: 1440 frames for 48 s; video = audio duration; 0 decode errors; −14 ±0.5 LUFS; TP ≤ −1 dBTP; xcorr lag 0;
no unintended near-black frames; no static run > 2 s outside planned holds; seam diff ≈ median frame diff; SSIM ≥ ~0.95.

## 6. Delivery (orchestrator → Kürşat)
- [ ] Send `out/<slug>.mp4` + `out/contact_sheet.png` with a short Turkish summary: what QC fixed, which facts were checked,
      remaining small issues, open choices (with the default already chosen), size/length. Say **"Hiçbir yerde paylaşılmadı."**
- [ ] Never post. If Kürşat approves posting, he does it or explicitly asks for it.
- [ ] Commit sources (not videos): `build_spec.py`, specs, plan, sources, brief, retention map, QC report, boards, `out/{upload.json,cover.png,contact_sheet.png}`, engine + tests.
