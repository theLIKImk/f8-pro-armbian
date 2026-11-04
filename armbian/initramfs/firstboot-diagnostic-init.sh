#!/bin/sh
# First-kernel diagnostic: RAM logs only, no physical partition mounts or writes.
PATH=/bin:/sbin:/usr/bin:/usr/sbin
export PATH
umask 077
fail() {
    echo "F8 FIRSTBOOT STOP: $*" >/dev/kmsg 2>/dev/null || true
    while :; do sleep 60; done
}
mkdir -p /dev /proc /sys /run
mount -t devtmpfs devtmpfs /dev || fail devtmpfs
mount -t proc proc /proc || fail proc
mount -t sysfs sysfs /sys || fail sysfs
mount -t tmpfs -o mode=0700 tmpfs /run || fail tmpfs
echo 'F8 6.1 FIRSTBOOT INIT REACHED' >/dev/kmsg
exec >/run/steps.log 2>&1
[ "$(uname -r)" = '6.1.172-f8-pro-armbian-eval' ] || fail release
mkdir -p /run/logdisk /sys/kernel/config
mount -t vfat -o loop /f8-firstboot-logs.img /run/logdisk || fail ram-logdisk
echo 'RAM diagnostic snapshot. No physical partitions mounted or written.' >/run/logdisk/README.TXT
uname -a >/run/logdisk/KERNEL.TXT
cat /proc/cmdline >/run/logdisk/CMDLINE.TXT
cat /proc/iomem >/run/logdisk/IOMEM.TXT
cat /proc/partitions >/run/logdisk/PARTS.TXT
cat /proc/device-tree/model >/run/logdisk/MODEL.TXT
cat /proc/device-tree/compatible >/run/logdisk/COMPAT.BIN
attempt=0
while [ "$attempt" -lt 30 ]; do
    [ -n "$(ls /sys/class/udc 2>/dev/null)" ] && [ -b /dev/mmcblk0 ] && break
    sleep 1
    attempt=$((attempt+1))
done
ls -l /dev/mmcblk* /sys/class/udc >/run/logdisk/DEVICES.TXT 2>&1
dmesg >/run/logdisk/DMESG.TXT
cp /run/steps.log /run/logdisk/STEPS.TXT
sync
umount /run/logdisk || fail close-log-snapshot
mount -t configfs configfs /sys/kernel/config || fail configfs
g=/sys/kernel/config/usb_gadget/f8_firstboot
mkdir -p "$g" || fail gadget
echo 0x2207 >"$g/idVendor"
echo 0x0010 >"$g/idProduct"
mkdir -p "$g/strings/0x409" "$g/configs/c.1/strings/0x409"
echo F8PRO61FIRSTBOOT >"$g/strings/0x409/serialnumber"
echo 'F8-PRO evaluation' >"$g/strings/0x409/manufacturer"
echo '6.1 firstboot RAM logs' >"$g/strings/0x409/product"
echo 'Read-only log snapshot' >"$g/configs/c.1/strings/0x409/configuration"
echo 100 >"$g/configs/c.1/MaxPower"
mkdir -p "$g/functions/mass_storage.0" || fail mass-storage
echo 1 >"$g/functions/mass_storage.0/lun.0/ro"
echo 1 >"$g/functions/mass_storage.0/lun.0/removable"
echo /f8-firstboot-logs.img >"$g/functions/mass_storage.0/lun.0/file" || fail ram-lun
ln -s "$g/functions/mass_storage.0" "$g/configs/c.1/" || fail link-function
udc=$(ls /sys/class/udc 2>/dev/null | head -n 1)
[ -n "$udc" ] || fail no-udc
echo "$udc" >"$g/UDC" || fail bind-udc
echo 'F8 FIRSTBOOT READONLY RAM LOG DISK READY' >/dev/kmsg
while :; do sleep 60; done
