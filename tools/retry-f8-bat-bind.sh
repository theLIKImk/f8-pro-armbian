#!/bin/sh
# 模块加载了，但绑定服务 inactive —— oneshot 已跑过但 ExecStart 可能失败。
# 手动重跑看错误：
sudo -n systemctl start f8-battery-cw2015.service 2>&1
systemctl is-active f8-battery-cw2015.service
sudo -n journalctl -u f8-battery-cw2015 -b --no-pager | tail -5
echo "---手动执行:"
echo cw2015 0x62 > /sys/bus/i2c/devices/i2c-6/new_device 2>&1
echo "rc=$?"
sleep 2
ls /sys/class/power_supply/
echo DONE
