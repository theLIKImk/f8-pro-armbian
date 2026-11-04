#!/bin/sh
set -e
cd /var/tmp/f8-pro-armbian/native-power-pm1
# ITS 引用的 incbin 是相对当前目录的文件名（fdt/kernel/ramdisk/resource）——都在
ls
mkimage -f boot.its boot.img
ls -la boot.img
sha256sum boot.img
echo BUILD_OK_V2
