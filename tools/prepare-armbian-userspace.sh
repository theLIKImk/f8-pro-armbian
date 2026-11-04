#!/bin/sh
# Debian base evaluation for the Armbian port. No Armbian BSP/board claim yet.
set -eu
base=/var/tmp/f8-pro-armbian
rootfs="$base/rootfs-trixie-evaluation"
mkdir -p "$base"
if [ -f "$base/userspace-stage1.ok" ]; then
    printf 'Signed ARM64 base stage one already completed\n'
    exit 0
fi
if [ -e "$rootfs" ]; then
    printf 'Existing incomplete evaluation rootfs; inspect userspace-stage1.log before resuming\n' >&2
    exit 1
fi
debootstrap --foreign --arch=arm64 --variant=minbase \
    --components=main,non-free-firmware \
    --keyring=/usr/share/keyrings/debian-archive-keyring.gpg \
    trixie "$rootfs" https://deb.debian.org/debian > "$base/userspace-stage1.log" 2>&1
test -f "$rootfs/debootstrap/debootstrap"
touch "$base/userspace-stage1.ok"
printf 'Signed Debian ARM64 stage one completed; not an Armbian image\n'
