#!/usr/bin/env bash
# Delivery integrity: frame count, durations (video == audio), decode errors, codec/colour tags, faststart.
# Usage: tools/qc/integrity.sh out/<slug>.mp4
V="$1"
ffprobe -v error -count_frames -show_entries stream=codec_type,codec_name,profile,width,height,r_frame_rate,nb_read_frames,duration,pix_fmt,color_primaries,color_transfer,color_space,sample_rate,bit_rate -of compact "$V"
echo "decode errors: $(ffmpeg -v error -i "$V" -f null - 2>&1 | wc -l)"
python3 - "$V" <<'PY'
import sys; b=open(sys.argv[1],'rb').read(1<<20); m=b.find(b'moov'); d=b.find(b'mdat')
print('faststart:', 'yes' if m!=-1 and (d==-1 or m<d) else 'NO (moov after mdat)')
PY
ls -l "$V" | awk '{printf "size %.1f MB\n", $5/1e6}'
