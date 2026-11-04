#!/bin/sh
# Compile missing drivers against the exact official header package + symvers.
set -eu
project=/mnt/d/Netdisk/Other/F8-PRO/archlinux
base=/var/tmp/f8-pro-armbian
headers="$base/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx"
work="$base/extra-modules-6.1.115"
test -f "$headers/Module.symvers"
test -f "$headers/include/generated/autoconf.h"
mkdir -p "$work"
cp "$project/analysis/armbian/source-audit/linux-rockchip/drivers/power/supply/cw2015_battery.c" "$work/"
cp "$project/analysis/armbian/source-audit/linux-rockchip/drivers/power/supply/bq25890_charger.c" "$work/"
printf 'obj-m += cw2015_battery.o\nobj-m += bq25890_charger.o\n' > "$work/Makefile"
# Build only missing host tools from these headers; full modules_prepare needs
# architecture sources omitted by the official package.
if [ ! -x "$headers/scripts/mod/modpost" ]; then
    python3 "$project/tools/prepare-official-module-tools.py" > "$work/host-tools.log" 2>&1
fi
set +e
make -C "$headers" M="$work" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- \
    KERNELRELEASE=6.1.115-vendor-rk35xx -j2 modules > "$work/build.log" 2>&1
status=$?
set -e
mkdir -p "$project/analysis/armbian/extra-modules"
cp "$work/build.log" "$project/analysis/armbian/extra-modules/"
printf 'Official-header external module build exit: %s\n' "$status"
exit "$status"
