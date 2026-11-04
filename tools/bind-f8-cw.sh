#!/bin/sh
# 模块已加载。手动绑定 i2c 设备（0x62）：
echo cw2015 6-0062 | sudo -n tee /sys/bus/i2c/devices/i2c-6/new_device
sleep 3
echo "=== power_supply ==="
ls /sys/class/power_supply/
echo "=== 6-0062 设备 ==="
cat /sys/bus/i2c/devices/6-0062/name 2>/dev/null
ls /sys/bus/i2c/devices/6-0062/power_supply/ 2>/dev/null
echo "=== dmesg ==="
sudo -n dmesg | grep -i cw2015 | tail -5
echo DONE
