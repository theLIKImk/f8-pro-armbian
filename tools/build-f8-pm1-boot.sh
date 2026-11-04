#!/bin/sh
# 构建 pm1 BOOT：基于 U5 构建树，仅改 chosen/bootargs：
# - 去掉 cpufreq.off=1
# - 去掉 initcall_blacklist=rockchip_cpufreq_driver_init
# 其余全部保留（含 f8_usb_u1=1 —— 当前系统就是带着它跑的，U5 profile 由 rootfs
# 服务决定而非该参数；保守起见一并保留，避免任何行为差异）。
set -e
SRC=/var/tmp/f8-pro-armbian/native-usb-u5
DST=/var/tmp/f8-pro-armbian/native-power-pm1
rm -rf "$DST"; mkdir -p "$DST"
cp "$SRC/kernel" "$SRC/ramdisk" "$SRC/resource" "$DST/"
cp "$SRC/fdt" "$DST/fdt"
OLD=$(fdtget "$DST/fdt" /chosen bootargs)
NEW=$(echo "$OLD" | sed 's/ cpufreq\.off=1//; s/ initcall_blacklist=rockchip_cpufreq_driver_init//')
echo "OLD: $OLD"
echo "NEW: $NEW"
fdtput -t s "$DST/fdt" /chosen bootargs "$NEW"
# 校验
GOT=$(fdtget "$DST/fdt" /chosen bootargs)
case "$GOT" in
  *cpufreq.off*|*initcall_blacklist*) echo "FAIL: cmdline still has flags"; exit 1;;
esac
echo "VERIFIED: $GOT"
# ITS 更新描述
sed 's/NATIVE DESKTOP T1 NOT APPROVED/POWER MODE PM1 cpufreq enabled/' "$SRC/boot.its" > "$DST/boot.its"
cd "$DST"
mkimage -f boot.its boot.img
ls -la boot.img
sha256sum boot.img
echo BUILD_OK
