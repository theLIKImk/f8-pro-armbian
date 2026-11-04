#!/bin/sh
# Diagnostic initramfs: prepare RAM log collector, then boot the real Arch PID1.
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
umask 077
mount -t devtmpfs devtmpfs /dev 2>/dev/null || true
mount -t proc proc /proc 2>/dev/null || true
mount -t sysfs sysfs /sys 2>/dev/null || true
mkdir -p /run
mount -t tmpfs -o mode=0755 tmpfs /run 2>/dev/null || true
mkdir -p /run/f8diag /mnt/arch
chmod 0700 /run/f8diag
exec >/run/f8diag/HANDOFF.TXT 2>&1
echo 'F8-PRO REAL ARCH PID1 HANDOFF'
echo 'Normal boot writes machine identity/journal to rootfs. No formatting.'
attempt=0
while [ ! -b /dev/mmcblk0p6 ] && [ "$attempt" -lt 45 ]; do
    sleep 1
    attempt=$((attempt+1))
done
if ! mount -t ext4 -o rw /dev/mmcblk0p6 /mnt/arch; then
    echo 'ROOTFS RW MOUNT FAILED' >/run/f8-phase
    /f8-monitor --usb-log-monitor &
    while :; do sleep 60; done
fi
if [ ! -x /mnt/arch/usr/lib/systemd/systemd ] || [ ! -f /mnt/arch/etc/arch-release ]; then
    echo 'ARCH PID1 FILE CHECK FAILED' >/run/f8-phase
    /f8-monitor --usb-log-monitor &
    while :; do sleep 60; done
fi
cp /f8-logs.img /run/f8diag/logs.img
cp /f8-monitor /run/f8diag/monitor
cp /f8-snapshot.sh /run/f8diag/snapshot.sh
cp /usr/bin/busybox /run/f8diag/busybox
cp /usr/bin/mount /run/f8diag/mount
cp /usr/bin/umount /run/f8diag/umount
cp /lib/ld-linux-aarch64.so.1 /run/f8diag/ld.so
cp -a /usr/lib /run/f8diag/lib
if [ -f /f8-wifi-fix.py ]; then
    timeout 20 chroot /mnt/arch /usr/bin/python3 - </f8-wifi-fix.py >/run/f8diag/WIFIFIX.TXT 2>&1
    printf '\nexit_code=%s\n' "$?" >>/run/f8diag/WIFIFIX.TXT
fi
chmod 0700 /run/f8diag/monitor /run/f8diag/snapshot.sh
uname -a >/run/f8diag/KERNELID.TXT
cat /proc/cmdline >/run/f8diag/CMDLINE.TXT
dd if=/dev/mmcblk0 of=/run/f8diag/GPT.BIN bs=512 count=68 2>/run/f8diag/GPTREAD.TXT
echo 'ARCH PID1 STARTING' >/run/f8-phase
for filesystem in dev proc sys run; do
    if ! mount --move "/$filesystem" "/mnt/arch/$filesystem"; then
        echo "Move mount failed: $filesystem"
        while :; do sleep 60; done
    fi
done
# Both helpers get the target root and its moved /run; the original rootfs init
# wrapper is intentionally bypassed so the actual systemd binary becomes PID1.
chroot /mnt/arch /run/f8diag/monitor --arch-log-monitor &
chroot /mnt/arch /run/f8diag/ld.so --library-path /run/f8diag/lib /run/f8diag/busybox sh /run/f8diag/snapshot.sh &
echo 'EXECUTING SWITCH_ROOT TO ARCH SYSTEMD'
exec switch_root /mnt/arch /usr/lib/systemd/systemd --log-target=kmsg --log-level=debug
