#!/bin/sh
# 只重载 sensor 模块（不碰 CIF/DPHY —— 避开 Oops 禁令）
echo "=== before: v4l-subdev count ==="
ls /sys/class/video4linux/ | grep -c subdev
echo "=== rmmod gc5035 ==="
sudo -n rmmod gc5035 2>&1
echo "=== modprobe gc5035 ==="
sudo -n modprobe gc5035 2>&1
sleep 3
echo "=== after: subdev count & media0 sensor ==="
ls /sys/class/video4linux/ | grep -c subdev
sudo -n media-ctl -d /dev/media0 -p 2>/dev/null | grep -iE 'gc5035' | head -3
echo "=== dmesg tail ==="
sudo -n dmesg | tail -6
echo DONE
