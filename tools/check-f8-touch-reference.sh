#!/bin/sh
# Only compile serialized reference arrays; no driver linked, loaded or enabled.
set -eu
project=/mnt/d/Netdisk/Other/F8-PRO/archlinux
profile="$project/armbian/touch/reference-r8-shuping"
work=/var/tmp/f8-pro-armbian/touch-reference
mkdir -p "$work"
aarch64-linux-gnu-gcc -c -O0 -fno-toplevel-reorder "$profile/compile-reference.c" -o "$work/profile.o"
aarch64-linux-gnu-objcopy --dump-section ".rodata=$work/firmware.bin" \
    --dump-section ".data=$work/algorithm.bin" "$work/profile.o" "$work/profile-copy.o"
cmp "$profile/firmware-reference.bin" "$work/firmware.bin"
cmp "$profile/algorithm-reference.bin" "$work/algorithm.bin"
python3 "$project/tools/report-f8-touch-reference.py"
