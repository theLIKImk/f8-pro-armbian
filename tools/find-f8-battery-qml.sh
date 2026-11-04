#!/bin/sh
# org.kde.plasma.battery.so 插件已存在（powerdevil 包）！
# 缺的只是 QML UI 部分（batterymonitor qml）。查它属于谁：
lz4 -dc /var/lib/apt/lists/ports.ubuntu.com_dists_resolute_Contents-arm64.lz4 2>/dev/null | grep -E 'org/kde/plasma/private/batterymonitor|plasma/battery/contents' | head -8
echo "---"
ls /usr/lib/aarch64-linux-gnu/qt6/qml/org/kde/plasma/private/batterymonitor/ 2>/dev/null
echo DONE
