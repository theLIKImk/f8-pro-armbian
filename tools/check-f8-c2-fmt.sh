#!/bin/sh
echo "=== v4l2-ctl 试帧时 rkisp 侧日志 ==="
sudo -n dmesg | grep -iE 'rkisp' | grep -viE 'apparmor' | tail -15
echo "=== 先设格式再取帧（标准流程）==="
# mainpath 输出格式需先设置。GC5035 是 1152x864? 查 sensor 支持格式与 ISP 输出：
sudo -n v4l2-ctl -d /dev/video22 --list-formats-ext 2>&1 | head -12
echo "---video31:"
sudo -n v4l2-ctl -d /dev/video31 --list-formats-ext 2>&1 | head -12
echo DONE
