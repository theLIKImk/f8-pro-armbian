#!/bin/sh
# 前摄路线A验证：video31（rkisp1-vir0 mainpath，GC5035）固定参数直出
# 1. 设置固定曝光（防自动飘）：手动 exposure/gain + 关 AEC/AGC
echo "=== 前摄 sensor subdev 控件 ==="
sudo -n v4l2-ctl -d /dev/v4l-subdev2 --list-ctrls 2>/dev/null | head -8
sudo -n v4l2-ctl -d /dev/v4l-subdev3 --list-ctrls 2>/dev/null | head -8
echo "=== 找 gc5035 的 subdev ==="
for s in /sys/class/video4linux/v4l-subdev*; do
  n=$(cat $s/name 2>/dev/null)
  case "$n" in *gc5035*|*m01*) echo "$s: $n";; esac
done
echo MARKER_DONE
