#!/bin/sh
# v4l-subdev 里没有 gc5035/ov8858 subdev！sensor 驱动绑定了但没注册 v4l2 subdev？
# 查 sensor 驱动 probe 的完整 dmesg（错误行）：
sudo -n dmesg | grep -iE 'gc5035|ov8858' | grep -viE 'supply|dummy|Looking' | head -12
echo "---ls modinfo of subdev count:"
ls /sys/class/video4linux/ | wc -l
echo "--- sensor driver state:"
cat /sys/bus/i2c/devices/5-0037/uevent
cat /sys/bus/i2c/devices/5-0036/uevent
echo DONE
