#!/bin/bash
# C3 步骤2：增量编译 Image（后台，12核）
set -e
KB=/var/tmp/f8-pro-armbian/kernel-config-build
cd "$KB"
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-
# 检查编译器
which aarch64-linux-gnu-gcc || { echo NO_CROSS_GCC; exit 1; }
aarch64-linux-gnu-gcc --version | head -1
# 增量编译（之前已完整编译过，只重编受影响部分）
nohup make -j10 Image > /tmp/c3-build.log 2>&1 &
echo "BUILD_PID=$!"
echo BG_STARTED
