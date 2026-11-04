#!/bin/sh
set -eu
rootfs=/var/tmp/f8-pro-armbian/rootfs-trixie-evaluation
printf 'ROOT ARCH\n'
chroot "$rootfs" dpkg --print-architecture
printf 'INPUT BYTES\n'
head -n 3 /var/tmp/f8-pro-armbian/wayland-packages.resolved-input | od -An -tx1
printf 'ROOT PACKAGE LISTS\n'
ls -lh "$rootfs/var/lib/apt/lists"
printf 'KWIN POLICY\n'
chroot "$rootfs" apt-cache policy kwin-wayland
