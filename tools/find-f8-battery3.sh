#!/bin/sh
# 有 libbatterymonitorplugin.so（plasma-workspace-data 46 个 plasmoids 之一？）
# 但 /usr/share/plasma/plasmoids/org.kde.plasma.battery 目录不存在。
# data 包 46 个 plasmoids —— 看有没有 battery 在其中（前面 ls 只显示 13 个！）：
dpkg -L plasma-workspace-data | grep 'plasmoids/org.kde' | head -20
echo "=== 实际目录数 ==="
ls /usr/share/plasma/plasmoids/ | wc -l
echo DONE
