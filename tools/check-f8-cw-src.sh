#!/bin/sh
# 设备上就有完整 headers！直接在设备上编译 cw2015 驱动（官方 mainline 驱动，
# 源码来自 vendor 6.1 树 drivers/power/supply/cw2015_battery.c —— 检查 headers 里有没有）:
ls /usr/src/linux-headers-6.1.115-vendor-rk35xx/drivers/power/supply/ 2>/dev/null | grep -i cw
echo "---"
grep -rn 'cw2015' /usr/src/linux-headers-6.1.115-vendor-rk35xx/drivers/power/supply/Makefile 2>/dev/null
echo DONE
