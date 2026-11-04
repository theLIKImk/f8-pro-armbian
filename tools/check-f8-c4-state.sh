echo "BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)"
systemctl is-system-running
ls /sys/class/video4linux | wc -l
for d in /sys/bus/i2c/devices/5-0036 /sys/bus/i2c/devices/5-0037; do
  echo "$d -> $(readlink $d/driver 2>/dev/null | xargs -r basename)"
done
ls /sys/kernel/debug/v4l2-async/ 2>/dev/null
echo MARKER_DONE
