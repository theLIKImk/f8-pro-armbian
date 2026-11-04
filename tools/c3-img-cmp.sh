#!/bin/bash
A=/var/tmp/f8-pro-armbian/camera-c2/kernel
B=/var/tmp/f8-pro-armbian/camera-c3/kernel
for s in bcmdhd panthor rkcif rkisp panel_simple; do
  c2=$(strings "$A" | grep -c "$s")
  c3=$(strings "$B" | grep -c "$s")
  echo "$s: C2=$c2 C3=$c3"
done
echo ---
ls -la "$A" "$B"
