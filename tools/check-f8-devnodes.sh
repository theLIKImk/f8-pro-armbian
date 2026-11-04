#!/bin/sh
# /dev/video* 打不开 No such device —— minor 号没对上设备。设备确实在 sysfs。
# 这是 udev 权限/设备节点问题？看 /dev/video0 的主次设备号 vs sysfs：
ls -la /dev/video0 /dev/video22 2>/dev/null
cat /sys/class/video4linux/video0/dev 2>/dev/null
cat /sys/class/video4linux/video22/dev 2>/dev/null
echo "---"
# 也许 /dev 下根本没这些节点（容器/udev 竞态）:
ls /dev/video* 2>/dev/null | head -8
echo DONE
