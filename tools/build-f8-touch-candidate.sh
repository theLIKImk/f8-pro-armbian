#!/bin/sh
# Compile one isolated driver object; do not modify the frozen source/config.
set -eu
project=/mnt/d/Netdisk/Other/F8-PRO/archlinux
source_dir=/var/tmp/f8-pro-armbian/linux-rockchip-config
build_dir=/var/tmp/f8-pro-armbian/kernel-config-build
work=/var/tmp/f8-pro-armbian/touch-driver-candidate
test "$(git -C "$source_dir" rev-parse HEAD)" = 85233a85b67928000afc2e966bab86a8c414f1b4
mkdir -p "$work"
cp "$project/armbian/touch/candidate-r8-shuping/gsl3673.c" "$work/"
cp "$project/armbian/touch/reference-r8-shuping/f8-pro-r8-shuping-reference.h" "$work/"
printf 'obj-m := gsl3673.o\nccflags-y += -I%s/drivers/input/touchscreen\n' "$source_dir" > "$work/Makefile"
set +e
make -C "$source_dir" O="$build_dir" M="$work" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- gsl3673.o > "$work/build.log" 2>&1
status=$?
set -e
cp "$work/build.log" "$project/armbian/touch/candidate-r8-shuping/"
test "$status" -eq 0 || exit "$status"
aarch64-linux-gnu-readelf -h "$work/gsl3673.o" > "$work/elf-header.txt"
cp "$work/build.log" "$work/elf-header.txt" "$project/armbian/touch/candidate-r8-shuping/"
sha256sum "$work/gsl3673.o"
python3 "$project/tools/report-f8-touch-candidate.py"
