#!/bin/sh
echo "BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)"
echo "=== camera start service log ==="
sudo -n journalctl -u f8-camera-start.service -b --no-pager -q 2>/dev/null | tail -15
echo "=== sensor drivers / chips ==="
for d in 5-0037 5-0036; do
  echo "-- $d: $(readlink /sys/bus/i2c/devices/$d/driver 2>/dev/null | xargs -r basename)"
done
echo "=== media links ==="
for m in /dev/media*; do
  echo "-- $m:"
  sudo -n media-ctl -d "$m" -p 2>/dev/null | grep -E 'driver|entity' | head -6
done
echo "=== v4l2 full node list ==="
ls /sys/class/video4linux/
echo "=== cmdline camera mark ==="
cat /proc/cmdline | tr ' ' '\n' | grep -E 'camera|f8_' | head -5
echo DONE
