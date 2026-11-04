#!/bin/sh
echo "=== 前摄现状检查 ==="
echo "--- gc5035 sensor:"
ls /sys/bus/i2c/devices/5-0037/driver >/dev/null 2>&1 && echo bound
echo "--- ISP30（前摄用的 ISP0/vir0）实体:"
sudo -n media-ctl -d /dev/media2 -p 2>/dev/null | head -8
echo "--- 原厂 GC5035 IQ 位置与 sub_scene:"
find /opt/f8-pro-camera -iname '*gc5035*' 2>/dev/null
sudo -n grep -l 'scene_isp21' /opt/f8-pro-camera/aiq-v6-c4/iqfiles/*.json 2>/dev/null | head -2
echo "--- GC5035 IQ 的 sub_scene 值:"
for f in /opt/f8-pro-camera/aiq-v6-c4/iqfiles/*.json; do
  s=$(sudo -n grep -o '"sub_scene"[^,]*' "$f" 2>/dev/null | head -1)
  n=$(basename "$f")
  [ -n "$s" ] && echo "$n: $s"
done
echo "--- 后摄成功参照（fps14 派生IQ结构）:"
ls /opt/f8-pro-camera/aiq-v6-c4/iqfiles-fps14/ 2>/dev/null
echo MARKER_DONE
