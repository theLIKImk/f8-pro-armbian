#!/bin/sh
# "Extra parameters" —— 之前失败的 "cw2015 6-0062" 和 "cw2015_battery 6-0062"
# 其实是设备名里有多个 token？"cw2015-battery" 通过了 rc=0？看设备是否已创建：
ls /sys/bus/i2c/devices/ | grep -E '0062'
echo "---"
ls /sys/class/power_supply/
echo "---"
dmesg | grep -iE 'cw2015|6-0062' | tail -5
echo DONE
