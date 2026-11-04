#!/bin/bash
# 修复：fbcon.o 损坏（上次编译被中断导致 archive 成员损坏）
KB=/var/tmp/f8-pro-armbian/kernel-config-build
cd "$KB"
rm -f drivers/video/fbdev/core/fbcon.o drivers/video/fbdev/core/built-in.a
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-
LOG=/var/tmp/f8-pro-armbian/c3-build.log
setsid nohup make -j10 Image > "$LOG" 2>&1 < /dev/null &
disown
sleep 5
echo "restarted: $(pgrep -f 'make -j10 Image' | head -1)"
tail -2 "$LOG"
