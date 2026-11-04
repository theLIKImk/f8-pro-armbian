#!/bin/sh
echo "BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)"
head -c 60 /proc/device-tree/model 2>/dev/null; echo
echo "--- V4L2 nodes:"
ls /sys/class/video4linux/ 2>/dev/null | head -10
echo "--- camera service:"
systemctl is-active f8-camera-start.service 2>&1
echo "--- sensors bound:"
ls /sys/bus/i2c/devices/5-0037/driver 2>/dev/null && echo GC5035-bound || echo GC5035-not-bound
ls /sys/bus/i2c/devices/5-0036/driver 2>/dev/null && echo OV8858-bound || echo OV8858-not-bound
echo DONE
