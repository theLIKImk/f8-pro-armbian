#!/bin/sh
# Read-only inventory; no network profiles or private keys.
set -u
printf 'HOST\n'
cat /proc/sys/kernel/hostname
printf 'FILESYSTEM\n'
findmnt -n -o SOURCE,FSTYPE,SIZE,AVAIL /
lsblk -b -o NAME,SIZE,TYPE,FSTYPE,PARTUUID,MOUNTPOINT /dev/mmcblk0
printf 'BOOT HELPERS\n'
ps -eo comm,args | awk '/f8diag|early-init|systemd --log/ && !/awk/ { print }'
printf 'INIT LINK\n'
readlink /usr/bin/init
printf 'MAC POLICY\n'
nmcli -g 802-11-wireless.cloned-mac-address connection show f8-pro-test-wifi
printf 'GRAPHICS NODES\n'
ls -l /dev/dri /dev/mali0 /dev/fb0
printf 'DISPLAY STATUS\n'
for connector in /sys/class/drm/card*-*; do
    [ -r "$connector/status" ] || continue
    printf '%s ' "$connector"
    cat "$connector/status"
    test ! -r "$connector/modes" || cat "$connector/modes"
done
printf 'PACKAGES\n'
pacman -Q systemd glibc networkmanager openssh e2fsprogs mesa libglvnd plasma-workspace sddm 2>&1 || true
printf 'POWER\n'
for supply in /sys/class/power_supply/*; do
    printf '%s\n' "$supply"
    for attribute in status capacity online; do
        if [ -r "$supply/$attribute" ]; then
            printf '%s=' "$attribute"
            cat "$supply/$attribute"
        fi
    done
done
exit 0
