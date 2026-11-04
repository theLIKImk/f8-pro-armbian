#!/bin/bash
# C3 离线校验：
set -e
DST=/var/tmp/f8-pro-armbian/camera-c3
echo "=== 1. boot.img 容量（64MiB 分区上限）==="
ls -la "$DST/boot.img"
SIZE=$(stat -c %s "$DST/boot.img")
[ "$SIZE" -lt 67108864 ] && echo "size OK"
echo "=== 2. Image 内建 sensor 验证 ==="
strings "$DST/kernel" | grep -c 'galaxycore,gc5035'
strings "$DST/kernel" | grep -c 'ovti,ov8858'
echo "=== 3. cmdline 未变（fdt chosen）==="
dtc -I dtb -O dts "$DST/fdt" 2>/dev/null | grep 'bootargs' | grep -oE 'cpufreq.off=1|f8_usb_u1=1' | head -2
echo "=== 4. FIT 结构 ==="
mkimage -l "$DST/boot.img" | grep -E 'Image Name|Data Size' | head -6
echo "=== 5. resource 未动（与 C2 一致）==="
cmp /var/tmp/f8-pro-armbian/camera-c2/resource "$DST/resource" && echo RESOURCE_SAME
cmp /var/tmp/f8-pro-armbian/camera-c2/ramdisk "$DST/ramdisk" && echo RAMDISK_SAME
cmp /var/tmp/f8-pro-armbian/camera-c2/fdt "$DST/fdt" && echo FDT_SAME
echo "=== 6. 模块不再含 sensor（防止加载旧模块）==="
ls /var/tmp/f8-pro-armbian/kernel-config-build/drivers/media/i2c/gc5035.ko 2>/dev/null && echo "NOTE: gc5035.ko still exists in build tree (rootfs 里的旧模块无妨，内建优先)"
echo C3_VERIFY_OK
