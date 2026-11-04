#!/bin/sh
# Diagnostic initramfs: never starts vendor recovery or mounts physical storage RW.
umask 077
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
mount -t devtmpfs devtmpfs /dev 2>/dev/null || true
mount -t proc proc /proc 2>/dev/null || true
mount -t sysfs sysfs /sys 2>/dev/null || true
mkdir -p /run
mount -t tmpfs -o mode=0700 tmpfs /run 2>/dev/null || true
exec >/run/f8-steps.log 2>&1
echo 'F8-PRO USB BOOTLOG INIT START'
echo 'READ ONLY ROOTFS; NO VENDOR RECOVERY OR RC SCRIPTS'
echo 'PREPARING LOG DISK' >/run/f8-phase
/f8-monitor --usb-log-monitor &
mkdir -p /run/logdisk /mnt/arch /sys/kernel/config
if ! mount -t vfat -o loop /f8-logs.img /run/logdisk; then
    echo 'RAM LOG DISK MOUNT FAILED' >/run/f8-phase
    while :; do sleep 60; done
fi
printf 'Diagnostic logs from RAM. Physical rootfs was only mounted ro,noload.\r\n' >/run/logdisk/README.TXT
uname -a >/run/logdisk/KERNELID.TXT
cat /proc/cmdline >/run/logdisk/CMDLINE.TXT
cat /proc/partitions >/run/logdisk/PARTS.TXT
# Primary GPT metadata only; never expose a physical disk as a USB LUN.
dd if=/dev/mmcblk0 of=/run/logdisk/GPT.BIN bs=512 count=68 2>/run/logdisk/GPTREAD.TXT
ls -l /dev/mmcblk* /dev/dri /dev/fb* /sys/class/udc >/run/logdisk/DEVICES.TXT 2>&1
blkid >/run/logdisk/BLKID.TXT 2>&1 || true
echo 'CHECKING ROOTFS READ ONLY' >/run/f8-phase
attempt=0
while [ ! -b /dev/mmcblk0p6 ] && [ "$attempt" -lt 45 ]; do
    sleep 1
    attempt=$((attempt+1))
done
if mount -t ext4 -o ro,noload /dev/mmcblk0p6 /mnt/arch; then
    echo 'ROOTFS READONLY MOUNT OK' >/run/logdisk/ROOTFS.TXT
    cat /mnt/arch/etc/os-release >>/run/logdisk/ROOTFS.TXT 2>&1
    ls -ld /mnt/arch/sbin /mnt/arch/usr/bin/init /mnt/arch/usr/lib/systemd/systemd >>/run/logdisk/ROOTFS.TXT 2>&1
    sha256sum /mnt/arch/usr/libexec/f8-pro/early-init >>/run/logdisk/ROOTFS.TXT 2>&1
    wc -c /mnt/arch/etc/machine-id >>/run/logdisk/ROOTFS.TXT 2>&1
    ls -l /mnt/arch/var/log/journal >>/run/logdisk/ROOTFS.TXT 2>&1
    # Native-kernel execution probes only; never start target PID1/services.
    timeout 15 chroot /mnt/arch /usr/bin/true >/run/logdisk/RUNTRUE.TXT 2>&1
    printf '\nexit_code=%s\n' "$?" >>/run/logdisk/RUNTRUE.TXT
    timeout 15 chroot /mnt/arch /usr/libexec/f8-pro/early-init --self-test >/run/logdisk/RUNINIT.TXT 2>&1
    printf '\nexit_code=%s\n' "$?" >>/run/logdisk/RUNINIT.TXT
    timeout 15 chroot /mnt/arch /usr/lib/systemd/systemd --version >/run/logdisk/RUNSYS.TXT 2>&1
    printf '\nexit_code=%s\n' "$?" >>/run/logdisk/RUNSYS.TXT
    # Copy at most four <= 8 MiB journals. Never copy profiles or host private keys.
    count=0
    for journal in /mnt/arch/var/log/journal/*/*.journal /mnt/arch/var/log/journal/*/*.journal~; do
        [ -f "$journal" ] || continue
        bytes=$(wc -c <"$journal")
        [ "$bytes" -le 8388608 ] || continue
        [ "$count" -lt 4 ] || break
        count=$((count+1))
        cp "$journal" "/run/logdisk/J$count.journal"
    done
    umount /mnt/arch || echo 'Read-only rootfs unmount failed'
else
    echo 'ROOTFS READONLY MOUNT FAILED' >/run/logdisk/ROOTFS.TXT
fi
mount -t pstore pstore /sys/fs/pstore 2>/dev/null || true
count=0
for record in /sys/fs/pstore/*; do
    [ -f "$record" ] || continue
    [ "$count" -lt 4 ] || break
    count=$((count+1))
    head -c 65536 "$record" >"/run/logdisk/PSTORE$count.TXT"
done
mount -t configfs configfs /sys/kernel/config 2>/dev/null || true
g=/sys/kernel/config/usb_gadget/f8_bootlog
mkdir -p "$g"
echo 0x2207 >"$g/idVendor"
echo 0x0010 >"$g/idProduct"
mkdir -p "$g/strings/0x409"
echo F8PROBOOTLOG >"$g/strings/0x409/serialnumber"
echo 'F8-PRO diagnostic' >"$g/strings/0x409/manufacturer"
echo 'F8-PRO boot logs' >"$g/strings/0x409/product"
mkdir -p "$g/configs/c.1/strings/0x409"
echo 'Read-only boot logs' >"$g/configs/c.1/strings/0x409/configuration"
echo 250 >"$g/configs/c.1/MaxPower"
mkdir -p "$g/functions/mass_storage.0"
echo 1 >"$g/functions/mass_storage.0/lun.0/ro"
echo 1 >"$g/functions/mass_storage.0/lun.0/removable"
ln -s "$g/functions/mass_storage.0" "$g/configs/c.1/" || true
attempt=0
udc=$(ls /sys/class/udc 2>/dev/null | head -n 1)
while [ -z "$udc" ] && [ "$attempt" -lt 30 ]; do
    sleep 1
    attempt=$((attempt+1))
    udc=$(ls /sys/class/udc 2>/dev/null | head -n 1)
done
printf 'UDC=%s\n' "$udc" >/run/logdisk/USB.TXT
ls -l /sys/class/udc >>/run/logdisk/USB.TXT 2>&1
dmesg >/run/logdisk/DMESG.TXT
cp /run/f8-steps.log /run/logdisk/STEPS.TXT
sync
if ! umount /run/logdisk; then
    echo 'RAM LOG DISK UNMOUNT FAILED' >/run/f8-phase
    while :; do sleep 60; done
fi
if [ -z "$udc" ]; then
    echo 'USB UDC NOT FOUND' >/run/f8-phase
elif ! echo /f8-logs.img >"$g/functions/mass_storage.0/lun.0/file"; then
    echo 'USB LOG FILE BIND FAILED' >/run/f8-phase
elif ! echo "$udc" >"$g/UDC"; then
    echo 'USB CONTROLLER BIND FAILED' >/run/f8-phase
else
    echo 'USB LOG DISK READY' >/run/f8-phase
fi
while :; do sleep 60; done
