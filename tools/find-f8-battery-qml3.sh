#!/bin/sh
# 桌面托盘里现在显示什么？先看当前系统托盘状态 + plasmashell 配置：
# Plasma 6.6 battery applet 实际是 C++ 插件 org.kde.plasma.battery.so +
# QML 从 plasma-workspace 的 /usr/share/plasma/plasmoids/org.kde.plasma.private.batterymonitor?
# 直接全盘找 battery applet QML：
find /usr/share/plasma /usr/lib/aarch64-linux-gnu/qt6/qml -iname '*battery*' 2>/dev/null
echo "---"
# 检查系统托盘当前条目配置：
grep -A5 'battery' /home/f8test/.config/plasma-org.kde.plasma.desktop-appletsrc 2>/dev/null | head -10 || echo no-user-mention
echo DONE
