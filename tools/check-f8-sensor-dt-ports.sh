#!/bin/sh
# 没有 v4l2 async 错误。sensor subdev 缺失但 async notifier "completed" —— 
# 这说明 CIF/DPHY 的 notifier 认为全部匹配完成，但 sensor subdev 根本没注册。
# 可能性：DT 里 sensor 端口（port/graph）声明丢失或端点 remote 指向错误 ——
# C2 改动时"删除 sensor 上的重复 pinctrl 声明"，会不会也动了 ports？
# 检查运行 DT 中 sensor 节点的 ports：
sudo -n ls /proc/device-tree/i2c@fead0000/gc5035@37/ 2>/dev/null
echo "---ports 子树:"
sudo -n ls /proc/device-tree/i2c@fead0000/gc5035@37/ports/ 2>/dev/null || echo NO-PORTS
sudo -n ls /proc/device-tree/i2c@fead0000/gc5035@37/port/ 2>/dev/null || echo NO-PORT
echo DONE
