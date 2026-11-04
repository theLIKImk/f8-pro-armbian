#!/bin/sh
# RAW 链已接通。重新取帧（格式已设过 NV12 800x600）：
echo "=== video22 (ISP0 mainpath) ==="
sudo -n timeout 12 v4l2-ctl -d /dev/video22 --stream-mmap=4 --stream-count=1 --stream-to=/tmp/f8-isp0.raw --stream-poll 2>&1
echo "rc=$?"
ls -la /tmp/f8-isp0.raw 2>/dev/null
echo "=== video31 (ISP1 mainpath) ==="
sudo -n timeout 12 v4l2-ctl -d /dev/video31 --stream-mmap=4 --stream-count=1 --stream-to=/tmp/f8-isp1.raw --stream-poll 2>&1
echo "rc=$?"
ls -la /tmp/f8-isp1.raw 2>/dev/null
echo "=== dmesg ==="
sudo -n dmesg | grep -iE 'rkisp|rkcif|gc5035|ov8858' | grep -viE 'apparmor|dummy|Looking' | tail -10
echo ALLDONE
