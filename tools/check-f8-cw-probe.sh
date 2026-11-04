#!/bin/sh
# 设备实例化成功！但 "Failed to get supply state: -19" (ENODEV) —— 驱动需要
# vdd supply regulator，DT 里没有所以失败。看 power_supply 出现了吗：
ls /sys/class/power_supply/
echo "---"
ls /sys/bus/i2c/devices/6-0062/
echo "---"
dmesg | grep cw2015 | tail -3
echo DONE
