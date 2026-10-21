#!/usr/bin/env bash
# CRF 18 archive master (what `bitloop render` writes by default) + the near-lossless CRF 4 intermediate that feeds
# tools/encode_upload.sh and SSIM checks. Usage: tools/make_master.sh projects/<slug>   (run from repo root)
set -euo pipefail
P="${1%/}"; SLUG="$(basename "$P")"; BL="$(cd "$(dirname "$0")/.." && pwd)/bitloop/bitloop.sh"
mkdir -p "$P/out"
"$BL" render "$P/spec.json" -o "$P/out/${SLUG}_master.mp4" --package          # CRF 18 + cover.png + upload.json (cover from meta.cover_t)
"$BL" render "$P/spec.json" -o "/tmp/${SLUG}_crf4.mp4" --crf 4                  # intermediate, not committed
"$(dirname "$0")/encode_upload.sh" "/tmp/${SLUG}_crf4.mp4" "$P/out/${SLUG}.mp4"
python "$(dirname "$0")/finalize_package.py" "$P"
echo "upload: $P/out/${SLUG}.mp4   master: $P/out/${SLUG}_master.mp4   intermediate: /tmp/${SLUG}_crf4.mp4"
