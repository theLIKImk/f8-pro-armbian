#!/bin/sh
# Invalid argument —— 驱动的 of_match/id_table 可能要求 DT compatible 或设备名不同。
# 查驱动支持的设备名与 compatible：
strings /lib/modules/6.1.115-vendor-rk35xx/updates/cw2015_battery.ko | grep -iE 'cw2015|cw2013|cellwise' | head -10
echo "---"
strings /var/tmp/f8-pro-armbian/extra-modules-6.1.115/cw2015_battery.ko | grep -iE 'cw20|cellwise' | head -10
echo DONE
