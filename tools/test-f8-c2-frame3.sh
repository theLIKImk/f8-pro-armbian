#!/bin/sh
echo "T1"
cat /sys/class/video4linux/video22/name 2>/dev/null
echo "T2"
sudo -n timeout 8 v4l2-ctl -d /dev/video22 --stream-mmap=4 --stream-count=1 --stream-to=/tmp/f8-isp0.raw --stream-poll
echo "T3 rc=$?"
ls -la /tmp/f8-isp0.raw 2>/dev/null
echo "T4"
sudo -n dmesg | tail -4
echo "T5 ALLDONE"
