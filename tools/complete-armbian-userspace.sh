#!/bin/sh
# Complete only the isolated Debian base used to evaluate Armbian userspace.
set -eu
base=/var/tmp/f8-pro-armbian
rootfs="$base/rootfs-trixie-evaluation"
test -f "$base/userspace-stage1.ok"
test -f /proc/sys/fs/binfmt_misc/qemu-aarch64
if [ ! -f "$base/userspace-stage2.ok" ]; then
    chroot "$rootfs" /debootstrap/debootstrap --second-stage > "$base/userspace-stage2.log" 2>&1
    chroot "$rootfs" dpkg --print-architecture | grep -qx arm64
    touch "$base/userspace-stage2.ok"
fi
printf 'Isolated ARM64 Debian base completed; Armbian BSP not installed yet\n'
