#!/bin/sh
echo "=== 内核电源类设备 ==="
ls /sys/class/power_supply/ 2>/dev/null || echo none
for p in /sys/class/power_supply/*/; do
  echo "-- $p"
  cat "$p/type" 2>/dev/null
  cat "$p/manufacturer" 2>/dev/null
  head -c 100 "$p/capacity" 2>/dev/null; echo
done
echo "=== upower ==="
which upower 2>/dev/null && upower -e 2>/dev/null
systemctl status upower --no-pager -n 2 2>&1 | head -5
echo "=== 相关包 ==="
dpkg -l 2>/dev/null | grep -E 'upower|powerdevil|plasma-workspace|kinfocenter' | awk '{print $2, $3}'
echo "=== plasma battery widget 文件 ==="
ls /usr/share/plasma/plasmoids/org.kde.plasma.battery/ 2>/dev/null | head -3 || echo no-battery-widget
echo DONE
