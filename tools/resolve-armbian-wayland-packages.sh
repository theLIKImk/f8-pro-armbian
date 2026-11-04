#!/bin/sh
# Signed metadata + dependency simulation in the isolated ARM64 evaluation root.
set -eu
project=/mnt/d/Netdisk/Other/F8-PRO/archlinux
base=/var/tmp/f8-pro-armbian
rootfs="$base/rootfs-trixie-evaluation"
test -f "$base/userspace-stage2.ok"
cat > "$rootfs/etc/apt/sources.list" <<'EOF'
deb http://deb.debian.org/debian trixie main non-free-firmware
deb http://deb.debian.org/debian trixie-updates main non-free-firmware
deb http://security.debian.org/debian-security trixie-security main non-free-firmware
EOF
# Service installation is not performed here; no private credentials are copied.
chroot "$rootfs" apt-get -o Acquire::Languages=none update > "$base/wayland-apt-update.log" 2>&1
tr -d '\r' < "$project/armbian/wayland-packages.txt" | grep -v '^#' | sed '/^$/d' > "$base/wayland-packages.resolved-input"
xargs chroot "$rootfs" apt-get -s --no-install-recommends install \
    < "$base/wayland-packages.resolved-input" > "$base/wayland-apt-simulation.log" 2>&1
mkdir -p "$project/analysis/armbian/userspace"
cp "$base/wayland-apt-update.log" "$base/wayland-apt-simulation.log" \
    "$project/analysis/armbian/userspace/"
chroot "$rootfs" dpkg-query -W > "$project/analysis/armbian/userspace/base-packages.tsv"
printf 'Wayland dependency simulation completed on signed ARM64 repositories\n'
