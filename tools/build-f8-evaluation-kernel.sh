#!/bin/sh
# Base Armbian source evaluation kernel, not the official 26.8.3 ABI.
set -eu
project=/mnt/d/Netdisk/Other/F8-PRO/archlinux
source_dir=/var/tmp/f8-pro-armbian/linux-rockchip-config
build_dir=/var/tmp/f8-pro-armbian/kernel-config-build
exec 9>/var/tmp/f8-pro-armbian/custom-kernel-build.lock
flock -n 9 || { echo 'Custom kernel build already running' >&2; exit 1; }
test "$(git -C "$source_dir" rev-parse HEAD)" = 85233a85b67928000afc2e966bab86a8c414f1b4
test -f "$source_dir/mm/mmap.c"
cd "$source_dir"
scripts/config --file "$build_dir/.config" --set-str LOCALVERSION -f8-pro-armbian-eval
scripts/config --file "$build_dir/.config" --disable LOCALVERSION_AUTO
make O="$build_dir" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig > "$build_dir/evaluation-config.log" 2>&1
set +e
make O="$build_dir" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j4 Image > "$build_dir/evaluation-image.log" 2>&1
status=$?
set -e
mkdir -p "$project/analysis/armbian/kernel-build"
printf '%s\n' "$status" > "$project/analysis/armbian/kernel-build/image-build.exit"
cp "$build_dir/evaluation-config.log" "$build_dir/evaluation-image.log" "$project/analysis/armbian/kernel-build/"
cp "$build_dir/.config" "$project/analysis/armbian/kernel-build/evaluation.config"
if [ "$status" -eq 0 ]; then
    python3 "$project/tools/export-f8-evaluation-image.py"
fi
printf 'Evaluation Image build exit: %s\n' "$status"
exit "$status"
