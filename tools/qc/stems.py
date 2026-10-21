"""Render isolated music stems from a spec to check that a voice is actually audible (e.g. a whisper/lookahead voice
sitting ~31 dB under the lead was a real QC finding) or that two voices don't mask each other.
Usage: python tools/qc/stems.py projects/<slug>/spec.json /tmp/<slug>_stem --keep lead,bass [--drums] [--logo] [--sfx]
Writes <prefix>.wav: the raw synth mix (pre-master) of only those voices. NOTE: bitloop.music.synth peak-normalises its
output, so absolute levels of two separate stems are NOT comparable. To check masking/audibility, keep both voices in the
SAME stem (e.g. --keep lead,whisper) and compare their pitch bands in a spectrum/FFT, or listen."""
import argparse, copy, json, os, tempfile
from _common import ROOT  # noqa: F401  (puts bitloop on sys.path)
from bitloop import spec as S
from bitloop.music import synth

ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("prefix"); ap.add_argument("--keep", required=True)
ap.add_argument("--drums", action="store_true"); ap.add_argument("--logo", action="store_true"); ap.add_argument("--sfx", action="store_true"); a = ap.parse_args()
keep = set(a.keep.split(","))
t = copy.deepcopy(json.load(open(a.spec, encoding="utf-8"))); mu = t["music"]
for k in list(mu.get("voices", {})):
    if k not in keep: mu["voices"][k] = None
for sec in mu.get("sections", []):
    if "voices" in sec: sec["voices"] = [v for v in sec["voices"] if v in keep]
    if not a.drums: sec["drums"] = "none"
if not a.drums: mu["drums"] = "none"
if not a.logo: mu["logo"] = False
if not a.sfx: mu["sfx"] = False
fd, tmp = tempfile.mkstemp(suffix=".json", dir=os.path.dirname(os.path.abspath(a.spec)))   # same dir: asset paths resolve
try:
    with os.fdopen(fd, "w", encoding="utf-8") as fh: json.dump(t, fh, ensure_ascii=False)
    synth(S.load(tmp), a.prefix + ".wav", music=True); print(a.prefix + ".wav")
finally:
    os.remove(tmp)
