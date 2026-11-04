#!/bin/bash
KB=/var/tmp/f8-pro-armbian/kernel-config-build
cd "$KB"
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-
setsid nohup make -j10 Image > /tmp/c3-build.log 2>&1 < /dev/null &
disown
sleep 3
echo "log exists: $(ls -la /tmp/c3-build.log)"
tail -3 /tmp/c3-build.log
