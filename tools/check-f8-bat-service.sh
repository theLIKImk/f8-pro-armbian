#!/bin/sh
echo "BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)"
echo "=== battery service ==="
systemctl is-active f8-battery-cw2015.service
systemctl status f8-battery-cw2015.service --no-pager -n 5 2>&1 | head -8
echo "=== module loaded? ==="
lsmod | grep cw2015 || echo MODULE_NOT_LOADED
echo "=== modules-load conf ==="
cat /etc/modules-load.d/f8-cw2015.conf 2>/dev/null || echo no-conf
echo "=== power_supply ==="
ls /sys/class/power_supply/
echo "=== journal for cw ==="
sudo -n journalctl -b --no-pager -q 2>/dev/null | grep -iE 'cw2015|new_device' | tail -5
echo DONE
