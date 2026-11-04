#!/bin/sh
# Explicitly board-bound online growth. Never creates filesystems or edits GPT.
set -eu
umask 077
[ "$(id -u)" -eq 0 ] && [ -f /etc/arch-release ] || exit 2
device=/dev/mmcblk0p6
[ "$(findmnt -n -o SOURCE /)" = "$device" ] || exit 2
[ "$(findmnt -n -o FSTYPE /)" = ext4 ] || exit 2
[ "$(blkid -s PARTUUID -o value "$device")" = 614e0000-0000-4b53-8000-1d28000054a9 ] || exit 2
[ "$(cat /sys/class/block/mmcblk0p6/start)" = 491520 ] || exit 2
[ "$(blockdev --getsize64 "$device")" = 246960619520 ] || exit 2
[ "$(blockdev --getro "$device")" = 0 ] || exit 2
[ "$(cat /sys/fs/ext4/mmcblk0p6/errors_count)" = 0 ] || exit 2
[ "$(cat /sys/class/power_supply/bq25890-charger/online)" = 1 ] || exit 2
[ "$(cat /sys/class/power_supply/cw2015-battery/capacity)" -ge 50 ] || exit 2
directory=/var/lib/f8-pro/maintenance
[ -f "$directory/config-backup-verified.sha256" ] || { echo 'Verified private backup required'; exit 2; }
grep -Eq '^[0-9a-f]{64}$' "$directory/config-backup-verified.sha256" || exit 2
header=$(dumpe2fs -h "$device" 2>/dev/null)
size=$(printf '%s\n' "$header" | awk '/^Block size:/ {print $3}')
before=$(printf '%s\n' "$header" | awk '/^Block count:/ {print $3}')
[ "$size" = 4096 ] || exit 2
target=$((246960619520 / size))
if [ "$before" = "$target" ]; then echo 'Already at full partition size'; exit 0; fi
[ "$before" = 524288 ] || { echo 'Unexpected filesystem size; stop for review'; exit 2; }
printf '%s\n' "$header" >"$directory/rootfs-before-growth.txt"
printf 'Growing existing ext4 from %s to %s blocks of %s bytes\n' "$before" "$target" "$size"
sync
resize2fs "$device" "$target"
dumpe2fs -h "$device" >"$directory/rootfs-after-growth.txt" 2>&1
after=$(awk '/^Block count:/ {print $3}' "$directory/rootfs-after-growth.txt")
[ "$after" = "$target" ] || exit 2
[ "$(cat /sys/fs/ext4/mmcblk0p6/errors_count)" = 0 ] || exit 2
[ "$(blockdev --getsize64 "$device")" = 246960619520 ] || exit 2
sha256sum -c /var/lib/f8-pro/boot-backup/identity-before-normal.sha256
df -h /
systemctl is-system-running
systemctl --failed --no-pager
echo 'Root filesystem growth verified; partition unchanged.'
