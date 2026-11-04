#!/bin/sh
# 好消息：系统托盘已经配置了 org.kde.plasma.battery 条目（knownItems/extraItems）！
# 问题只剩：当前没有任何电池设备（/sys/class/power_supply 只有 USB PD 的 tcpm-source），
# 没有 BAT 设备时 Plasma 自动隐藏电池图标。
# 所以"安装电池组件"的实际工作 = 让内核/upower 暴露电池设备。
# CW2015 电量计在 I2C 总线上，但 HANDOFF 记录"电池/充电/PD 用户明确暂缓"——
# 现在用户主动要求电池组件，先只读探测 I2C 总线上的 CW2015 是否可枚举：
echo "=== I2C 总线列表 ==="
sudo -n i2cdetect -l 2>/dev/null
echo "=== CW2015 通常在哪个总线（原厂 DT 记录） ==="
ls /sys/bus/i2c/devices/ 2>/dev/null | head -20
echo "=== 当前已绑定设备 ==="
for d in /sys/bus/i2c/devices/*/; do
  n=$(cat "$d/name" 2>/dev/null)
  echo "$d -> $n"
done
echo DONE
