#!/bin/sh
set -eu
[ "$(id -u)" -eq 0 ] && [ -f /etc/arch-release ] || exit 2
printf 'PID1: '
cat /proc/1/comm
arguments=$(tr '\000' ' ' </proc/1/cmdline)
printf 'PID1 arguments: %s\n' "$arguments"
case "$arguments" in *--log-level=debug*|*f8diag*) echo 'Diagnostic PID1 still active'; exit 2;; esac
[ ! -e /run/f8diag ] || { echo 'Diagnostic runtime remains'; exit 2; }
[ ! -d /sys/kernel/config/usb_gadget/f8_bootlog ] || { echo 'Diagnostic gadget remains'; exit 2; }
[ "$(readlink /usr/bin/init)" = ../lib/systemd/systemd ] || exit 2
sha256sum -c /var/lib/f8-pro/boot-backup/identity-before-normal.sha256
systemctl is-system-running
systemctl --failed --no-pager
ip -brief address show wlan0
printf 'ROOT SOURCE\n'
findmnt -n -o SOURCE,FSTYPE,OPTIONS /
printf 'PARTITION BYTES\n'
blockdev --getsize64 /dev/mmcblk0p6
printf 'PARTITION START\n'
cat /sys/class/block/mmcblk0p6/start
printf 'PARTUUID\n'
blkid -s PARTUUID -o value /dev/mmcblk0p6
printf 'FILESYSTEM HEADER\n'
dumpe2fs -h /dev/mmcblk0p6 2>/dev/null
printf 'ROOT ERROR COUNTER\n'
if [ -r /sys/fs/ext4/mmcblk0p6/errors_count ]; then cat /sys/fs/ext4/mmcblk0p6/errors_count; fi
printf 'POWER\n'
for path in /sys/class/power_supply/*/online /sys/class/power_supply/*/capacity; do
    [ ! -r "$path" ] || { printf '%s=' "$path"; cat "$path"; }
done
exit 0
