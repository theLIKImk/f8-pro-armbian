#!/bin/sh
# Invalid argument 可能因为驱动用 of only（无 i2c device id table legacy match）。
# 查驱动源码 id_table:
grep -A8 'i2c_device_id' /var/tmp/f8-pro-armbian/extra-modules-6.1.115/cw2015_battery.c | head -12
echo "---of_match:"
grep -A8 'of_match_table' /var/tmp/f8-pro-armbian/extra-modules-6.1.115/cw2015_battery.c | head -12
echo "---driver name:"
grep -E '\.name\s*=' /var/tmp/f8-pro-armbian/extra-modules-6.1.115/cw2015_battery.c | head -4
echo DONE
