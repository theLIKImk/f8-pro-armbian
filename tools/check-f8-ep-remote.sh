#!/bin/sh
# sensor 节点有旧式单 port/endpoint（不是 ports/）。查 endpoint 的 remote-endpoint
# 指向谁、以及 dphy1 的端口声明：
echo "== gc5035 endpoint remote:"
sudo -n fdtget /sys/firmware/fdt /i2c@fead0000/gc5035@37/port/endpoint remote-endpoint 2>/dev/null
echo "== ov8858:"
sudo -n fdtget /sys/firmware/fdt /i2c@fead0000/ov8858@36/port/endpoint remote-endpoint 2>/dev/null
echo "== dphy1 (找节点路径):"
sudo -n find /proc/device-tree -name 'csi2-dphy*' -maxdepth 2 2>/dev/null | head -3
echo DONE
