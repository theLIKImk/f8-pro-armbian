#!/bin/sh
# 先验证模块能在无 DT 节点的情况下 insmod（驱动会注册 i2c driver，等待设备）：
sudo -n modprobe cw2015_battery 2>&1
echo "modprobe rc=$?"
lsmod | grep cw2015 || echo not-loaded
echo "--- 尝试以 new_device 方式绑定（DT 暂无节点，用 sysfs 手动注册 i2c 设备）:"
# 这会创建 i2c 设备让驱动 probe —— 只读电量计，安全。
# 但注意：若 DT 后续加节点会重复。先用临时验证探测芯片能否被驱动识别：
echo cw2015 6-0062 | sudo -n tee /sys/bus/i2c/devices/i2c-6/new_device 2>&1
sleep 2
ls /sys/class/power_supply/
ls /sys/bus/i2c/devices/6-0062/ 2>/dev/null | grep -E 'name|power_supply' | head -5
echo DONE
