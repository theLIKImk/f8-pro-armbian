#!/bin/sh
# Runs in early RAM init or in the RAM-overlay target; never exports a real disk.
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
umask 077
stop() { echo "F8 R5 REPORT FAILED: $*" >/dev/kmsg 2>/dev/null || true; exit 1; }
mode=${1:-unknown}
image=/run/f8/eval-logs.img
[ -f "$image" ] && [ ! -L "$image" ] || stop ram-image-missing
mkdir -p /run/f8/logdisk /sys/kernel/config
mount -t vfat -o loop "$image" /run/f8/logdisk || stop ram-fat
disk=/run/f8/logdisk
printf 'R5 RAM-only userspace snapshot, mode=%s\n' "$mode" >"$disk/RESULT.TXT"
uname -a >"$disk/KERNEL.TXT"
cat /proc/cmdline >"$disk/CMDLINE.TXT"
cat /proc/mounts >"$disk/MOUNTS.TXT"
cat /proc/partitions >"$disk/PARTS.TXT"
cat /proc/1/comm >"$disk/PID1.TXT"
ls -l /proc/1/exe >>"$disk/PID1.TXT" 2>&1
cat /etc/os-release >"$disk/OSREL.TXT" 2>&1
cat /etc/f8-pro-evaluation >"$disk/MARKER.TXT" 2>&1
cat /sys/devices/system/cpu/online >"$disk/CPUONLINE.TXT"
cat /sys/class/tty/console/active >"$disk/CONSOLE.TXT" 2>&1
ls -l /sys/class/udc >"$disk/UDC.TXT" 2>&1
[ ! -f /run/f8/evaluation-steps.log ] || cp /run/f8/evaluation-steps.log "$disk/STEPS.TXT"
if [ "$mode" = systemd ]; then
    /usr/lib/systemd/systemd --version >"$disk/SYSVER.TXT" 2>&1
    timeout 10 systemctl --no-pager is-system-running >"$disk/SYSSTATE.TXT" 2>&1
    timeout 10 systemctl --no-pager show f8-evaluation.target -p ActiveState -p SubState >"$disk/TARGET.TXT" 2>&1
    timeout 10 systemctl --no-pager --failed >"$disk/FAILED.TXT" 2>&1
    {
        ls -ld / /run /etc /etc/os-release /run/systemd /run/systemd/journal /run/systemd/resolve
        stat -c '%a %u:%g %n' / /etc/systemd/system/f8-evaluation.* /usr/lib/systemd/system/f8-pro-ssh-hostkeys.service
    } >"$disk/PERMS.TXT" 2>&1
    timeout 20 systemd-run --wait --collect --unit=f8-nonroot-probe --property=User=nobody /usr/bin/test -r /etc/os-release >"$disk/NONROOT.TXT" 2>&1
    probe_status=$?
    printf 'exit_code=%s\n' "$probe_status" >>"$disk/NONROOT.TXT"
    timeout 10 systemctl --no-pager show systemd-resolved.service -p ActiveState -p SubState -p Result -p ExecMainStatus -p User -p WorkingDirectory >"$disk/RESOLVED.TXT" 2>&1
    timeout 10 journalctl -b -u systemd-resolved.service --no-pager >"$disk/DNSLOG.TXT" 2>&1
    {
        ls -l /dev/dri /dev/mali* /sys/class/drm
        ls -l /usr/lib/firmware/regulatory.db* /lib/firmware/regulatory.db*
        cat /proc/modules
    } >"$disk/DEVICES.TXT" 2>&1
    timeout 10 journalctl -b -n 350 --no-pager >"$disk/JOURNAL.TXT" 2>&1
fi
dmesg >"$disk/DMESG.TXT"
sync
umount "$disk" || stop close-fat
mount -t configfs configfs /sys/kernel/config 2>/dev/null || [ -d /sys/kernel/config/usb_gadget ] || stop configfs
g=/sys/kernel/config/usb_gadget/f8_evaluation_r5
mkdir -p "$g" || stop gadget
echo 0x2207 >"$g/idVendor"
echo 0x0010 >"$g/idProduct"
mkdir -p "$g/strings/0x409" "$g/configs/c.1/strings/0x409"
echo F8PRO61R5 >"$g/strings/0x409/serialnumber"
echo 'F8-PRO evaluation' >"$g/strings/0x409/manufacturer"
echo 'R5 RAM-overlay systemd logs' >"$g/strings/0x409/product"
echo 'Read-only RAM snapshot' >"$g/configs/c.1/strings/0x409/configuration"
echo 100 >"$g/configs/c.1/MaxPower"
mkdir -p "$g/functions/mass_storage.0" || stop function
echo 1 >"$g/functions/mass_storage.0/lun.0/ro"
echo 1 >"$g/functions/mass_storage.0/lun.0/removable"
echo "$image" >"$g/functions/mass_storage.0/lun.0/file" || stop ram-lun
ln -s "$g/functions/mass_storage.0" "$g/configs/c.1/" || stop link-function
udc=$(ls /sys/class/udc 2>/dev/null | head -n 1)
[ -n "$udc" ] || stop no-udc
echo "$udc" >"$g/UDC" || stop bind-udc
echo "F8 R5 USB SNAPSHOT READY mode=$mode" >/dev/kmsg
exit 0
