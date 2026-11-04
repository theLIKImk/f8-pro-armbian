#!/bin/sh
# ramoops 只有 5.10.160 原厂内核一次记录 —— vendor 6.1 内核没写 ramoops
# （DT 的 ramoops 节点可能没被 6.1 启用）。PM1 失败取证无内核日志。
# 采用分步法（每步单一变量）：
# PM1-A: 只去掉 initcall_blacklist=rockchip_cpufreq_driver_init，保留 cpufreq.off=1，
#        且 resource.img 不重建（沿用 U5 原件 —— 避开 resource 重建嫌疑）。
#        FIT 的 fdt 换成改过的（bootargs 少 initcall_blacklist）。
# 如果 PM1-A 起来了 → 说明 resource 重建是死因，或 initcall 无碍。
# 如果 PM1-A 也不起 → initcall_blacklist 是救命的（vendor cpufreq panic）。
set -e
SRC=/var/tmp/f8-pro-armbian/native-usb-u5
DST=/var/tmp/f8-pro-armbian/native-power-pm1a
rm -rf "$DST"; mkdir -p "$DST"
cp "$SRC/kernel" "$SRC/ramdisk" "$SRC/resource" "$DST/"   # resource 原封不动！
cp "$SRC/boot.its" "$DST/boot.its"
cp "$SRC/fdt" "$DST/fdt"
OLD=$(fdtget "$DST/fdt" /chosen bootargs)
NEW=$(echo "$OLD" | sed 's/ initcall_blacklist=rockchip_cpufreq_driver_init//')
echo "PM1-A NEW: $NEW"
fdtput -t s "$DST/fdt" /chosen bootargs "$NEW"
GOT=$(fdtget "$DST/fdt" /chosen bootargs)
case "$GOT" in
  *initcall_blacklist*) echo "FAIL still has blacklist"; exit 1;;
esac
case "$GOT" in
  *cpufreq.off=1*) echo "OK: cpufreq.off kept";;
  *) echo "FAIL: cpufreq.off lost"; exit 1;;
esac
sed 's/NATIVE DESKTOP T1 NOT APPROVED/POWER PM1A no-blacklist-only/' "$SRC/boot.its" > "$DST/boot.its"
cd "$DST" && mkimage -f boot.its boot.img
ls -la boot.img; sha256sum boot.img
echo BUILD_OK_PM1A
