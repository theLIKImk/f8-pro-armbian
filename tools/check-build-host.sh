#!/bin/sh
# Read-only tool inventory. Run inside the selected Linux build environment.
set -u
printf '%s\n' '=== system ==='
uname -a
cat /etc/os-release
id
printf '%s\n' '=== disk ==='
df -h / /mnt/d
printf '%s\n' '=== tools ==='
for tool in python3 bash tar bsdtar curl wget gpg gpgv gcc make aarch64-linux-gnu-gcc dtc mkimage qemu-aarch64-static qemu-aarch64 mke2fs debugfs e2fsck depmod readelf apt-get; do
    command -v "$tool" || true
done
printf '%s\n' '=== ARM emulation registration ==='
if [ -d /proc/sys/fs/binfmt_misc ]; then
    ls /proc/sys/fs/binfmt_misc
fi
