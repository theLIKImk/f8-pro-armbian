#!/bin/sh
# media0 里没有 sensor 实体 —— sensor 注册到了哪个 media？查 media2/3 及 dphy1 的
# 实际归属。rkisp0-vir0 是 media2。sensor 通常挂在 ISP 的 media 图。
sudo -n media-ctl -d /dev/media2 -p 2>/dev/null > /tmp/f8-m2.txt
grep -n -iE 'gc5035|ov8858' /tmp/f8-m2.txt | head -4
sudo -n media-ctl -d /dev/media3 -p 2>/dev/null > /tmp/f8-m3.txt
grep -n -iE 'gc5035|ov8858' /tmp/f8-m3.txt | head -4
echo "---检查 v4l-subdev 设备名与 sensor 对应:"
for s in /sys/class/video4linux/v4l-subdev*; do
  n=$(cat $s/name 2>/dev/null)
  echo "$s -> $n"
done
echo DONE
