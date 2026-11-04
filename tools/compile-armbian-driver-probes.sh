#!/bin/sh
# Selected ARM64 objects only, never installed or loaded on the tablet.
set -eu
project=/mnt/d/Netdisk/Other/F8-PRO/archlinux
source_dir=/var/tmp/f8-pro-armbian/linux-rockchip-config
build_dir=/var/tmp/f8-pro-armbian/kernel-config-build
test "$(git -C "$source_dir" rev-parse HEAD)" = 85233a85b67928000afc2e966bab86a8c414f1b4
test -f "$build_dir/.config"
git -C "$source_dir" -c http.version=HTTP/1.1 sparse-checkout add \
    /kernel/ /drivers/power/supply/ /drivers/regulator/ /drivers/mfd/ \
    /drivers/pinctrl/ /drivers/gpu/drm/panthor/ '/drivers/gpu/drm/*.h' /security/selinux/include/ /tools/include/ \
    /lib/vdso/ /arch/x86/entry/syscalls/
cd "$source_dir"
set +e
make O="$build_dir" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j2 \
    drivers/power/supply/cw2015_battery.o \
    drivers/power/supply/bq25890_charger.o \
    drivers/regulator/rk860x-regulator.o \
    drivers/mfd/rk806-core.o \
    drivers/pinctrl/pinctrl-rk806.o \
    drivers/gpu/drm/panthor/ > "$build_dir/driver-probes.log" 2>&1
status=$?
set -e
cp "$build_dir/driver-probes.log" "$project/analysis/armbian/kernel-config/"
printf 'Selected driver compile exit: %s\n' "$status"
exit "$status"
