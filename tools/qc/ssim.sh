#!/usr/bin/env bash
# SSIM of an encode vs its near-lossless source (upload target ≥ ~0.95 overall; check the min around flashes).
# Usage: tools/qc/ssim.sh <encoded.mp4> <reference_crf4.mp4>
ffmpeg -v error -i "$1" -i "$2" -lavfi "[0:v][1:v]ssim=stats_file=-" -f null - | awk '{for(i=1;i<=NF;i++) if($i ~ /^All:/){split($i,a,":"); s+=a[2]; n++; if(min==""||a[2]<min){min=a[2]; f=$1}}} END{printf "SSIM mean %.4f  min %.4f at %s  (%d frames)\n", s/n, min, f, n}'
