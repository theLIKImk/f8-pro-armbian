#!/bin/sh
# Signed repository runtime dependencies only; no desktop or GPU replacement.
set -eu
[ "$(id -u)" -eq 0 ] && [ -f /etc/arch-release ] || exit 2
[ "$(cat /proc/sys/kernel/osrelease)" = 5.10.160 ] || exit 2
[ -f /var/lib/f8-pro/keyring-ready ] || exit 2
available=$(df -Pk / | awk 'NR==2 {print $4}')
[ "$available" -gt 10485760 ] || { echo 'At least 10 GiB free required'; exit 2; }
# Keep a full system transaction instead of refreshing databases and installing
# single packages against partially updated base libraries. Factory FIT is external.
pacman -Syu --needed --noconfirm libdrm libx11 libxcb wayland
systemctl is-system-running
systemctl --failed --no-pager
pacman -Q libdrm libx11 libxcb wayland
