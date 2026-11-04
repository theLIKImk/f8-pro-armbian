#!/bin/sh
# Runs independently of target service success, against the real target root.
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
umask 077
# Keep basic logging independent of the target libc/mount implementation.
bb() { /run/f8diag/ld.so --library-path /run/f8diag/lib /run/f8diag/busybox "$@"; }
mount() { /run/f8diag/ld.so --library-path /run/f8diag/lib /run/f8diag/mount "$@"; }
umount() { /run/f8diag/ld.so --library-path /run/f8diag/lib /run/f8diag/umount "$@"; }
sleep() { bb sleep "$@"; }
mkdir() { bb mkdir "$@"; }
cp() { bb cp "$@"; }
cat() { bb cat "$@"; }
wc() { bb wc "$@"; }
timeout() { bb timeout "$@"; }
dmesg() { bb dmesg "$@"; }
ln() { bb ln "$@"; }
ls() { bb ls "$@"; }
head() { bb head "$@"; }
sync() { bb sync "$@"; }
exec >>/run/f8diag/SNAPSHOT.TXT 2>&1
sleep 60
echo 'COLLECTING ARCH BOOT LOGS' >/run/f8-phase
mkdir -p /run/f8diag/disk /sys/kernel/config
if ! mount -t vfat -o loop /run/f8diag/logs.img /run/f8diag/disk; then
    echo 'LOG DISK MOUNT FAILED' >/run/f8-phase
    exit 1
fi
out=/run/f8diag/disk
printf 'Logs after real Arch systemd PID1 handoff. Raw logs are private.\r\n' >"$out/README.TXT"
cp /run/f8diag/HANDOFF.TXT /run/f8diag/KERNELID.TXT /run/f8diag/CMDLINE.TXT /run/f8diag/GPT.BIN /run/f8diag/GPTREAD.TXT "$out/"
if [ -f /run/f8diag/WIFIFIX.TXT ]; then cp /run/f8diag/WIFIFIX.TXT "$out/"; fi
cat /etc/os-release >"$out/OS.TXT"
cat /proc/1/comm >"$out/PID1.TXT"
cat /proc/mounts >"$out/MOUNTS.TXT"
wc -c /etc/machine-id >"$out/MACHINE.TXT"
run() {
    name=$1; shift
    timeout 15 "$@" >"$out/$name" 2>&1
    printf '\nexit_code=%s\n' "$?" >>"$out/$name"
}
run STATE.TXT systemctl is-system-running
run FAILED.TXT systemctl --failed --no-pager
run SERVICES.TXT systemctl status --no-pager --full sshd NetworkManager systemd-resolved f8-pro-wifi f8-pro-bluetooth bluetooth f8-pro-keyring
run JOURNAL.TXT journalctl -b --no-pager -n 1200
run NET.TXT nmcli -f DEVICE,TYPE,STATE device status
run IP.TXT ip -brief address
run ROUTES.TXT ip route show
dmesg >"$out/DMESG.TXT" 2>&1
mount -t configfs configfs /sys/kernel/config 2>/dev/null || true
g=/sys/kernel/config/usb_gadget/f8_bootlog
mkdir -p "$g"
echo 0x2207 >"$g/idVendor"
echo 0x0010 >"$g/idProduct"
mkdir -p "$g/strings/0x409" "$g/configs/c.1/strings/0x409"
echo F8PROARCHLOG >"$g/strings/0x409/serialnumber"
echo 'F8-PRO diagnostic' >"$g/strings/0x409/manufacturer"
echo 'F8-PRO Arch boot logs' >"$g/strings/0x409/product"
echo 'Read-only Arch boot logs' >"$g/configs/c.1/strings/0x409/configuration"
echo 250 >"$g/configs/c.1/MaxPower"
mkdir -p "$g/functions/mass_storage.0"
echo 1 >"$g/functions/mass_storage.0/lun.0/ro"
echo 1 >"$g/functions/mass_storage.0/lun.0/removable"
ln -s "$g/functions/mass_storage.0" "$g/configs/c.1/" || true
udc=$(ls /sys/class/udc 2>/dev/null | head -n 1)
printf 'UDC=%s\n' "$udc" >"$out/USB.TXT"
cp /run/f8diag/SNAPSHOT.TXT "$out/SNAPSHOT.TXT"
sync
if ! umount /run/f8diag/disk; then
    echo 'LOG DISK UNMOUNT FAILED' >/run/f8-phase
    exit 1
fi
if [ -z "$udc" ]; then
    echo 'USB UDC NOT FOUND' >/run/f8-phase
elif ! echo /run/f8diag/logs.img >"$g/functions/mass_storage.0/lun.0/file"; then
    echo 'USB LOG FILE BIND FAILED' >/run/f8-phase
elif ! echo "$udc" >"$g/UDC"; then
    echo 'USB CONTROLLER BIND FAILED' >/run/f8-phase
else
    echo 'ARCH LOG SNAPSHOT READY' >/run/f8-phase
fi
