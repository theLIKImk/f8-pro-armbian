#!/bin/sh
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
umask 077
mkdir -p /run/f8
exec >/run/f8/network-start.log 2>&1
# Exact official module only; never load a module from the old Arch container.
modprobe bcmdhd firmware_path=/lib/firmware/ap6275p/fw_bcmdhd.bin nvram_path=/lib/firmware/ap6275p/nvram.txt || exit 1
nmcli general reload || true
for attempt in $(seq 1 40); do
    ip -4 -o addr show scope global | grep -q 'inet ' && exit 0
    sleep 2
done
echo 'No DHCP address yet; NetworkManager continues in background'
exit 0
