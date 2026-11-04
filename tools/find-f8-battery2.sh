#!/bin/sh
# plasma-workspace 装了但 plasmoids 列表里连 battery 都没有 —— 说明这是
# Ubuntu 精简的 plasma-workspace？检查官方 plasma-workspace 是否本该含 battery：
apt-cache show plasma-workspace 2>/dev/null | grep -E '^(Version|Size)' | head -2
echo "---"
# Plasma 6 里 battery widget 移到 plasma-workspace 主包。看 data 包：
dpkg -L plasma-workspace-data 2>/dev/null | grep -c plasmoids
dpkg -L plasma-workspace 2>/dev/null | grep -c plasmoids
echo "---"
# libbatterycontrol6 是 kded6 的电池控制模块库。kded 模块在？
dpkg -L plasma-workspace 2>/dev/null | grep -iE 'batterycontrol|brightness' | head
echo "---"
# 网络案：Ubuntu plasma-workspace 6.6.5 官方包含 org.kde.plasma.battery。确认没有其他目录：
find /usr/share/plasma -name '*battery*' 2>/dev/null | head
find /usr/lib/aarch64-linux-gnu/qt6/qml -iname '*batterymonitor*' 2>/dev/null | head -3
echo DONE
