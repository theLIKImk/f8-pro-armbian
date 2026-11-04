#!/bin/sh
echo "STEP1 nodes:"
cat /sys/class/video4linux/video22/name 2>/dev/null
cat /sys/class/video4linux/video31/name 2>/dev/null
echo "STEP2 try video22:"
sudo -n timeout 8 v4l2-ctl -d /dev/video22 --stream-mmap=4 --stream-count=1 --stream-to=/tmp/f8-isp0.raw --stream-poll
echo "rc=$?"
ls -la /tmp/f8-isp0.raw 2>/dev/null
echo "STEP3 dmesg tail:"
sudo -n dmesg | tail -5
echo ALLDONE
