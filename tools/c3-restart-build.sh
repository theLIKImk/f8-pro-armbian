#!/bin/bash
# 编译进程已消失且 /tmp 日志丢失（WSL 会话重启导致）。重新启动编译：
KB=/var/tmp/f8-pro-armbian/kernel-config-build
cd "$KB"
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-
LOG=/var/tmp/f8-pro-armbian/c3-build.log
setsid nohup make -j10 Image > "$LOG" 2>&1 < /dev/null &
disown
sleep 5
echo "PID: $(pgrep -f 'make -j10 Image' | head -1)"
tail -3 "$LOG"
echo BG_RESTARTED
