#!/bin/sh
# Intermediate minimal-core image. No desktop/BSP or tablet deployment claim.
set -eu
project=/mnt/d/Netdisk/Other/F8-PRO/archlinux
base=/var/tmp/f8-pro-armbian
rootfs="$base/rootfs-trixie-evaluation"
toolroot="$base/host-tools/root"
test -f "$base/evaluation-core.ok"
test -f "$rootfs/lib/modules/6.1.115-vendor-rk35xx/modules.dep"
! mountpoint -q "$rootfs/proc"
! mountpoint -q "$rootfs/sys"
# New, never-deployed evaluation identity; do not clone its build-time machine ID.
: > "$rootfs/etc/machine-id"
if [ -f "$rootfs/var/lib/dbus/machine-id" ] && [ ! -L "$rootfs/var/lib/dbus/machine-id" ]; then
    : > "$rootfs/var/lib/dbus/machine-id"
fi
export LD_LIBRARY_PATH="$toolroot/usr/lib/x86_64-linux-gnu:$toolroot/lib/x86_64-linux-gnu"
mkdir -p "$project/outputs/armbian/evaluation-core" "$project/analysis/armbian/userspace"
chroot "$rootfs" dpkg-query -W > "$project/analysis/armbian/userspace/evaluation-core-packages.tsv"
"$toolroot/usr/bin/mksquashfs" "$rootfs" "$project/outputs/armbian/evaluation-core/rootfs.squashfs" \
    -noappend -comp gzip -processors 2 -no-progress -wildcards \
    -e 'proc/*' 'sys/*' 'dev/*' 'run/*' 'tmp/*' 'var/log/*' 'var/cache/apt/archives/*.deb' \
    > "$base/evaluation-squashfs.log" 2>&1
"$toolroot/usr/bin/unsquashfs" -s "$project/outputs/armbian/evaluation-core/rootfs.squashfs" \
    > "$project/analysis/armbian/userspace/squashfs-summary.txt"
cd "$project/outputs/armbian/evaluation-core"
sha256sum rootfs.squashfs > SHA256SUMS
printf 'Intermediate minimal-core SquashFS built; not a complete Armbian or desktop image\n'
