#!/bin/sh
# 结论确认：Ubuntu 26.04 把 battery widget 拆出去了。找哪个包提供：
apt-cache search . 2>/dev/null | grep -iE '^plasma' | head -20
echo "=== 直接查 apt 提供者 ==="
apt-cache search org.kde.plasma.battery 2>/dev/null
apt-cache search batterymonitor 2>/dev/null
echo "=== Ubuntu 拆分包名可能是 plasma-workspace-applets* ==="
apt-cache search plasma 2>/dev/null | grep -iE 'applet|workspace' | head -10
echo DONE
