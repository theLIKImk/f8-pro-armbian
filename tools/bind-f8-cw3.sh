#!/bin/sh
# i2c_driver.name = "cw2015-battery"，id_table 条目 "cw2015"。
# new_device 用 driver name 或 id_table 名都可以，试 "cw2015-battery"：
echo cw2015-battery 6-0062 | sudo -n tee /sys/bus/i2c/devices/i2c-6/new_device 2>&1
sleep 3
ls /sys/class/power_supply/
echo "---dmesg:"
sudo -n dmesg | grep -iE 'cw2015|cw_bat' | tail -6
echo DONE
