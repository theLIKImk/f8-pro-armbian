#!/bin/sh
# 验证加固后的服务能正常跑（当前设备已绑定，new_device 重复会报 File exists
# —— 但 sh 的 for+break 会把它当失败重试。加 2>/dev/null 忽略已存在）：
sudo -n sh -c 'echo cw2015 0x62 > /sys/bus/i2c/devices/i2c-6/new_device' 2>&1
echo "rc=$? (Device busy=正常，已绑定)"
systemctl is-enabled f8-battery-cw2015
systemctl is-active f8-battery-cw2015
ls /sys/class/power_supply/
echo DONE
