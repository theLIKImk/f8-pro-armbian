#!/bin/sh
# 标准流程：先设格式（NV12 800x600），再取帧
echo "=== set format video22 ==="
sudo -n v4l2-ctl -d /dev/video22 --set-fmt-video=width=800,height=600,pixelformat=NV12 2>&1
echo "=== stream 1 frame video22 ==="
sudo -n timeout 10 v4l2-ctl -d /dev/video22 --stream-mmap=4 --stream-count=1 --stream-to=/tmp/f8-isp0.raw --stream-poll 2>&1
echo "rc=$?"
ls -la /tmp/f8-isp0.raw 2>/dev/null
echo "=== set format video31 ==="
sudo -n v4l2-ctl -d /dev/video31 --set-fmt-video=width=800,height=600,pixelformat=NV12 2>&1
echo "=== stream 1 frame video31 ==="
sudo -n timeout 10 v4l2-ctl -d /dev/video31 --stream-mmap=4 --stream-count=1 --stream-to=/tmp/f8-isp1.raw --stream-poll 2>&1
echo "rc=$?"
ls -la /tmp/f8-isp1.raw 2>/dev/null
echo "=== dmesg ==="
sudo -n dmesg | grep -iE 'rkisp|gc5035|ov8858|rkcif' | grep -viE 'apparmor|dummy|Looking' | tail -8
echo ALLDONE
