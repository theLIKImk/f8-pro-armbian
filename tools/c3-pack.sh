#!/bin/bash
set -e
KB=/var/tmp/f8-pro-armbian/kernel-config-build
DST=/var/tmp/f8-pro-armbian/camera-c3
rm -rf "$DST"
mkdir -p "$DST"
cp "$KB/arch/arm64/boot/Image" "$DST/kernel"
cp /var/tmp/f8-pro-armbian/camera-c2/ramdisk "$DST/ramdisk"
cp /var/tmp/f8-pro-armbian/camera-c2/fdt "$DST/fdt"
cp /var/tmp/f8-pro-armbian/camera-c2/resource "$DST/resource"
cp /var/tmp/f8-pro-armbian/camera-c2/boot.its "$DST/boot.its"
sed -i 's/NATIVE DESKTOP T1 NOT APPROVED/CAMERA C3 builtin sensors/' "$DST/boot.its"
cd "$DST"
mkimage -f boot.its boot.img
sha256sum boot.img
ls -la boot.img
echo C3_PACK_OK
