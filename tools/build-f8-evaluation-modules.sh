#!/bin/sh
# Full modules for the custom evaluation Image, never the official 6.1.115 ABI.
set -eu
project=/mnt/d/Netdisk/Other/F8-PRO/archlinux
source_dir=/var/tmp/f8-pro-armbian/linux-rockchip-config
build_dir=/var/tmp/f8-pro-armbian/kernel-config-build
reports="$project/analysis/armbian/kernel-build"
exec 9>"/var/tmp/f8-pro-armbian/custom-kernel-build.lock"
flock -n 9 || { echo 'Custom kernel build already running' >&2; exit 1; }
test "$(git -C "$source_dir" rev-parse HEAD)" = 85233a85b67928000afc2e966bab86a8c414f1b4
test "$(cat "$build_dir/include/config/kernel.release")" = 6.1.172-f8-pro-armbian-eval
test -f "$reports/verified-evaluation-image.json"
test -s "$build_dir/vmlinux.symvers"
mkdir -p "$reports"
date -u +%FT%TZ > "$reports/modules-build.started"
cd "$source_dir"
set +e
make O="$build_dir" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j4 modules \
    > "$build_dir/evaluation-modules.log" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$reports/modules-build.exit"
date -u +%FT%TZ > "$reports/modules-build.finished"
cp "$build_dir/evaluation-modules.log" "$reports/"
if [ "$status" -eq 0 ]; then
    test -s "$build_dir/Module.symvers"
    cp "$build_dir/Module.symvers" "$project/outputs/armbian/evaluation-kernel/Module.symvers"
fi
printf 'Custom evaluation modules build exit: %s\n' "$status"
exit "$status"
