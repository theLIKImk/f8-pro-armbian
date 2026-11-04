#!/bin/sh
# media0 = rkcif-mipi-lvds2（前摄 GC5035 的 CIF）。找它的 stream video 节点：
sudo -n media-ctl -d /dev/media0 -p 2>/dev/null | grep -B2 -A3 'stream_cif_mipi_id0' | head -14
echo M1
# video11-14 哪些属于 media0：
for v in 11 12 13 14 0 1 2 3; do
  d=$(cat /sys/class/video4linux/video$v/dev 2>/dev/null)
  n=$(cat /sys/class/video4linux/video$v/name 2>/dev/null)
  echo "video$v dev=$d name=$n"
done
echo MARKER_DONE
