#!/bin/sh
set -eu
project=/mnt/d/Netdisk/Other/F8-PRO/archlinux
rootfs=/var/tmp/f8-pro-armbian/rootfs-trixie-evaluation
out="$project/analysis/armbian/repository"
chroot "$rootfs" apt-cache show linux-image-vendor-rk35xx=26.8.3 \
    linux-headers-vendor-rk35xx=26.8.3 linux-dtb-vendor-rk35xx=26.8.3 > "$out/kernel-packages.deb822"
find "$rootfs/var/lib/apt/lists" -maxdepth 1 -type f -name '*armbian*' \
    -exec cp '{}' "$out/" ';'
printf 'Exported exact matching kernel package metadata and signed repository evidence\n'
