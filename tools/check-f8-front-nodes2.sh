#!/bin/sh
echo "=== mainpath nodes ==="
grep -H . /sys/class/video4linux/*/name | grep rkisp_mainpath
echo "=== media2 rkisp0 mainpath ==="
sudo -n media-ctl -d /dev/media2 -p 2>/dev/null | grep -A2 'rkisp_mainpath' | head -6
echo "=== media3 rkisp1 mainpath ==="
sudo -n media-ctl -d /dev/media3 -p 2>/dev/null | grep -A2 'rkisp_mainpath' | head -6
echo "=== video31 formats ==="
sudo -n v4l2-ctl -d /dev/video31 --list-formats-ext 2>&1 | head -12
echo MARKER_DONE
