#!/bin/sh
# F8-PRO 现场只读核验脚本 (2026-11-01)
echo "=== SYSTEM ==="
uname -a
head -3 /etc/os-release
hostname
echo "BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)"
uptime
echo "=== SYSTEMD ==="
systemctl is-system-running
systemctl --failed --no-legend
echo "=== USB OTG ==="
systemctl is-active f8-usb-otg.service 2>&1
systemctl is-enabled f8-usb-otg.service 2>&1
journalctl -u f8-usb-otg.service -b --no-pager | tail -8
echo "=== BLOCK / MOUNT ==="
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT,RO
echo "--- mounts of interest ---"
mount | grep -Ei 'mmcblk|exfat|/media|udisk' | head -10
echo "=== USB DEVICES ==="
lsusb 2>/dev/null | head -10
echo "=== UDISKS ==="
systemctl is-active udisks2 2>&1
systemctl is-enabled udisks2 2>&1
echo "=== TEMP ==="
cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -5
echo "=== DONE ==="
