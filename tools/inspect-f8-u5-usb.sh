#!/bin/sh
echo "=== USB EXTRA (sudo) ==="
journalctl -u f8-usb-otg.service -b --no-pager -q | tail -12
echo "=== LSUSB ==="
lsusb 2>/dev/null || echo lsusb-missing
echo "=== USB BUS DEVICES ==="
ls /sys/bus/usb/devices/
echo "=== ROLES ==="
for f in /sys/class/usb_role/*; do echo "$f: $(cat $f/role 2>/dev/null)"; done
echo "=== DWC3 BINDINGS ==="
ls -d /sys/bus/platform/drivers/dwc3/*/ 2>/dev/null
echo "=== USB STORAGE ==="
ls /sys/bus/usb/drivers/usb-storage/ 2>/dev/null
cat /proc/partitions
echo "=== DONE2 ==="
