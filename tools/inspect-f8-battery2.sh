#!/bin/sh
ls /usr/share/plasma/plasmoids/ | grep -iE 'batter|power'
echo "---"
dpkg -S /usr/share/plasma/plasmoids/org.kde.plasma.battery 2>/dev/null || echo "battery widget not owned / missing"
ls -d /usr/share/plasma/plasmoids/org.kde.plasma.battery 2>/dev/null || echo NO_BATTERY_DIR
echo "---"
dpkg -l | grep -E '^ii.*(powerdevil|plasma-workspace|upower)' | awk '{print $2, $3}'
echo "---"
systemctl --user is-active plasma-powerdevil 2>/dev/null || true
ps aux | grep -v grep | grep -iE 'powerdevil|kded' | head -5
echo DONE
