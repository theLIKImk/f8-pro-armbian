#!/bin/sh
# Board-specific normal initramfs. No diagnostic processes or USB functions.
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
umask 022
fail() {
    echo "F8-PRO initramfs: $*" >/dev/kmsg 2>/dev/null || true
    while :; do sleep 60; done
}
mount -t devtmpfs devtmpfs /dev 2>/dev/null || true
mount -t proc proc /proc || fail 'proc mount failed'
mount -t sysfs sysfs /sys || fail 'sysfs mount failed'
mkdir -p /run /mnt/arch
mount -t tmpfs -o mode=0755 tmpfs /run || fail 'run mount failed'
attempt=0
while [ ! -b /dev/mmcblk0p6 ] && [ "$attempt" -lt 45 ]; do
    sleep 1
    attempt=$((attempt+1))
done
[ -b /dev/mmcblk0p6 ] || fail 'expected board root partition missing'
mount -t ext4 -o rw /dev/mmcblk0p6 /mnt/arch || fail 'root mount failed'
[ -f /mnt/arch/etc/arch-release ] || fail 'root is not Arch'
[ -x /mnt/arch/usr/lib/systemd/systemd ] || fail 'systemd executable missing'
for filesystem in dev proc sys run; do
    mount --move "/$filesystem" "/mnt/arch/$filesystem" || fail 'mount move failed'
done
exec switch_root /mnt/arch /usr/lib/systemd/systemd --log-level=info
