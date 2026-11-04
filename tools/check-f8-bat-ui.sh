#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
echo "=== Plasma 现在能看到电池吗（upower DisplayDevice）==="
upower -i /org/freedesktop/UPower/devices/battery_cw2015_battery 2>/dev/null | head -12
echo "=== KDE 托盘 battery 图标已配置（appletsrc 已含 org.kde.plasma.battery）==="
echo "=== 请用户看屏幕右下角托盘是否出现电池图标 ==="
echo DONE
