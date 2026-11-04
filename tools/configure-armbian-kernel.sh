#!/bin/sh
# Source configuration check only: Armbian framework patch queue is not applied yet.
set -eu
project=/mnt/d/Netdisk/Other/F8-PRO/archlinux
source_dir=/var/tmp/f8-pro-armbian/linux-rockchip-config
build_dir=/var/tmp/f8-pro-armbian/kernel-config-build
expected=85233a85b67928000afc2e966bab86a8c414f1b4
test "$(git -C "$source_dir" rev-parse HEAD)" = "$expected"
mkdir -p "$build_dir"
git -C "$source_dir" sparse-checkout init --no-cone
cat > "$source_dir/.git/info/sparse-checkout" <<'EOF'
/*
!/*/
/scripts/
/include/
/arch/
!/arch/*/
/arch/arm64/
/**/Kconfig*
/**/Makefile*
EOF
git -C "$source_dir" -c http.version=HTTP/1.1 read-tree -mu HEAD
cp "$project/analysis/armbian/source-audit/build/config/kernel/linux-rk35xx-vendor.config" "$build_dir/base.config"
cd "$source_dir"
ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- KCONFIG_CONFIG="$build_dir/.config" \
    sh scripts/kconfig/merge_config.sh -m "$build_dir/base.config" \
    "$project/armbian/kernel/f8-pro-vendor-6.1.fragment" > "$build_dir/merge.log" 2>&1
make O="$build_dir" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig > "$build_dir/olddefconfig.log" 2>&1
mkdir -p "$project/analysis/armbian/kernel-config"
cp "$build_dir/.config" "$project/analysis/armbian/kernel-config/resolved-base.config"
cp "$build_dir/merge.log" "$build_dir/olddefconfig.log" "$project/analysis/armbian/kernel-config/"
printf 'Base kernel configuration resolved; framework patches and compilation still pending\n'
