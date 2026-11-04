#!/bin/sh
# compatible 是 cellwise,cw2015；i2c id_table 是 cw2015。
# new_device 需要 "驱动名 地址"——i2c_driver 的 name 是 "cw2015_battery"？还是 "cw2015"？
# 两个都试：
echo "=== 试 cw2015_battery ==="
echo cw2015_battery 6-0062 | sudo -n tee /sys/bus/i2c/devices/i2c-6/new_device 2>&1
sleep 2
ls /sys/class/power_supply/
sudo -n dmesg | grep -i cw | tail -4
echo DONE
