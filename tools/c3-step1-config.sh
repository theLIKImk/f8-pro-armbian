#!/bin/bash
# C3 构建：sensor 驱动内编（sed 改 .config）
set -e
KB=/var/tmp/f8-pro-armbian/kernel-config-build
cd "$KB"
sed -i 's/^CONFIG_VIDEO_GC5035=m$/CONFIG_VIDEO_GC5035=y/' .config
sed -i 's/^CONFIG_VIDEO_OV8858=m$/CONFIG_VIDEO_OV8858=y/' .config
grep -E 'CONFIG_VIDEO_GC5035|CONFIG_VIDEO_OV8858' .config
echo SED_OK
make olddefconfig 2>&1 | tail -2
grep -E 'CONFIG_VIDEO_GC5035|CONFIG_VIDEO_OV8858' .config
echo CONFIG_STEP_OK
