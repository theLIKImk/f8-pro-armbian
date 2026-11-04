#!/bin/sh
# Initramfs BusyBox only. Do not execute target userspace before switch_root.
set -eu
r=/mnt/root
mkdir -p "$r/usr/lib/firmware/ap6275p"
for file in /f8-live-firmware/*; do
    target="$r/usr/lib/firmware/ap6275p/${file##*/}"
    rm -f "$target"
    cp -a "$file" "$target"
done
echo 'F8SETUP: firmware copied in RAM; private provisioning deferred to systemd'
