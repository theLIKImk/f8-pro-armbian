#!/bin/sh
echo "=== rkcif video ENODEV 的真相检查 ==="
# rkcif video 注册需要 notifier complete。C2 的 notifier completed（2.6s）
# 但 22 个 video 节点 ENODEV。矛盾 → 也许 video 设备注册了但 video_register_device
# 因为 minor 冲突失败？检查 dmesg 里 video 注册错误：
sudo -n dmesg | grep -iE 'video.*regist|minor|video device' | tail -8
echo M1
# 直接看 /proc/devices 和 sysfs class 的 video 设备主次号：
cat /proc/devices | grep -E 'video|81'
echo M2
for v in /sys/class/video4linux/video0 /sys/class/video4linux/video22; do
  echo "$v dev=$(cat $v/dev 2>/dev/null) name=$(cat $v/name 2>/dev/null)"
done
echo MARKER_DONE
