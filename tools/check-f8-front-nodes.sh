#!/bin/sh
echo "=== 前摄可用的 ISP mainpath 节点确认 ==="
# 前摄 GC5035 -> rkisp1-vir0（sditf2->rkisp1）。查 rkisp1-vir0 的 mainpath video 节点：
for v in /sys/class/video4linux/video*; do
  n=$(cat $v/name 2>/dev/null)
  p=$(readlink -f $v)
  case "$n" in
    rkisp_mainpath) echo "$v: $n  path=$p";;
  esac
done
echo "=== media2 (rkisp0) 与 media3 (rkisp1) mainpath 归属 ==="
sudo -n media-ctl -d /dev/media2 -p 2>/dev/null | grep -B1 'video22' | head -3
sudo -n media-ctl -d /dev/media3 -p 2>/dev/null | grep -B1 'video31' | head -3
echo "=== 前摄支持格式（video31, rkisp1-vir0 mainpath）==="
sudo -n v4l2-ctl -d /dev/video31 --list-formats-ext 2>&1 | head -12
echo MARKER_DONE
