#!/bin/bash
KB=/var/tmp/f8-pro-armbian/kernel-config-build
rm -f "$KB/drivers/video/fbdev/core/fbcon.o" "$KB/drivers/video/fbdev/core/built-in.a"
cd "$KB" || exit 1
pwd
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-
LOG=/var/tmp/f8-pro-armbian/c3-build.log
setsid nohup make -j10 Image > "$LOG" 2>&1 < /dev/null &
disown
sleep 5
echo "pid: $(pgrep -f 'make -j10 Image' | head -1)"
tail -2 "$LOG"
