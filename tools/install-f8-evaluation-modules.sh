#!/bin/sh
# Install to a task-local module staging tree, never host /lib or the tablet.
set -eu
base=/var/tmp/f8-pro-armbian
project=/mnt/d/Netdisk/Other/F8-PRO/archlinux
source_dir="$base/linux-rockchip-config"
build_dir="$base/kernel-config-build"
staging="$base/custom-modules-install"
reports="$project/analysis/armbian/kernel-build"
exec 9>"$base/custom-kernel-build.lock"
flock -n 9 || { echo 'Custom kernel task already running' >&2; exit 1; }
test "$(cat "$reports/modules-build.exit")" = 0
test "$(cat "$build_dir/include/config/kernel.release")" = 6.1.172-f8-pro-armbian-eval
test "$(git -C "$source_dir" rev-parse HEAD)" = 85233a85b67928000afc2e966bab86a8c414f1b4
mkdir -p "$staging"
cd "$source_dir"
make O="$build_dir" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- \
    INSTALL_MOD_PATH="$staging" INSTALL_MOD_STRIP=1 modules_install \
    > "$build_dir/evaluation-modules-install.log" 2>&1
cp "$build_dir/evaluation-modules-install.log" "$reports/"
python3 "$project/tools/verify-f8-evaluation-modules.py"
