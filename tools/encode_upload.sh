#!/usr/bin/env bash
# Two-pass upload encode used for every @hayret.piksel delivery (see AGENTS.md "Delivery").
# Input should be a near-lossless render of the final spec, e.g.
#   bitloop/bitloop.sh render projects/<slug>/spec.json -o /tmp/<slug>_crf4.mp4 --crf 4
# Usage: tools/encode_upload.sh <near_lossless.mp4> <out_upload.mp4> [video_kbps=4400]
# Audio is copied untouched (it is already AAC 192k / 48 kHz from the render, mastered to -14 LUFS).
set -euo pipefail
IN="$1"; OUT="$2"; KBPS="${3:-4400}"
LOG="$(mktemp -d)/x264pass"
COMMON=(-c:v libx264 -preset slow -b:v "${KBPS}k" -maxrate 9000k -bufsize 9000k -tune animation
        -x264-params "no-deblock=1:psy-rd=0.6,0:aq-mode=2" -g 60 -r 30 -pix_fmt yuv420p -profile:v high -level 4.2
        -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv -passlogfile "$LOG")
ffmpeg -v error -y -i "$IN" "${COMMON[@]}" -pass 1 -an -f mp4 /dev/null
ffmpeg -v error -y -i "$IN" "${COMMON[@]}" -pass 2 -c:a copy -movflags +faststart "$OUT"
rm -rf "$(dirname "$LOG")"
ffprobe -v error -show_entries format=duration,size,bit_rate:stream=codec_name,width,height,r_frame_rate,color_primaries,pix_fmt \
        -of compact "$OUT"
