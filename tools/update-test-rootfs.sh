#!/bin/bash
# Update only the isolated ARM build tree. No host block devices are exposed.
set -euo pipefail
project=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
root=/var/tmp/f8-pro-archlinux-20261027/rootfs-vendor-staging
if [ "${F8_PRIVATE_MOUNT_NS:-}" != 1 ]; then
    exec unshare --mount --propagation private env F8_PRIVATE_MOUNT_NS=1 bash "$0"
fi
[ "$(id -u)" -eq 0 ] && [ -f "$root/etc/arch-release" ]
mkdir -p "$project/analysis/test-rootfs"
exec > >(tee "$project/analysis/test-rootfs/package-update.log") 2>&1
cleanup() {
    umount -R "$root/dev" 2>/dev/null || true
    umount "$root/proc" 2>/dev/null || true
    umount "$root" 2>/dev/null || true
}
trap cleanup EXIT
mount --bind "$root" "$root"
mkdir -p "$root/dev" "$root/proc"
mount -t tmpfs -o mode=0755,nosuid tmpfs "$root/dev"
for spec in 'null 1 3' 'zero 1 5' 'random 1 8' 'urandom 1 9' 'tty 5 0'; do
    read -r name major minor <<<"$spec"
    mknod -m 666 "$root/dev/$name" c "$major" "$minor"
done
mkdir "$root/dev/pts" "$root/dev/shm"
mount -t devpts -o newinstance,ptmxmode=0666,mode=0620 devpts "$root/dev/pts"
ln -s pts/ptmx "$root/dev/ptmx"
ln -s /proc/self/fd "$root/dev/fd"
mount -t proc -o nosuid,nodev,noexec proc "$root/proc"
# Replace only the candidate's resolver link, never follow it into the host.
if [ -L "$root/etc/resolv.conf" ]; then unlink "$root/etc/resolv.conf"; fi
cp /etc/resolv.conf "$root/etc/resolv.conf"
printf 'Server = https://mirrors.tuna.tsinghua.edu.cn/archlinuxarm/$arch/$repo\n' > "$root/etc/pacman.d/mirrorlist"
python3 - "$root/etc/pacman.conf" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1]); text = p.read_text()
if '\nDisableSandboxFilesystem\n' not in text:
    text = text.replace('[options]', '[options]\n# Vendor 5.10 and this WSL kernel have no usable Landlock.\nDisableSandboxFilesystem', 1)
p.write_text(text)
PY
chroot "$root" /usr/bin/pacman-key --init
chroot "$root" /usr/bin/pacman-key --populate archlinuxarm
# The board boots the separately preserved vendor FIT, not linux-aarch64.
# Remove the generic kernel and its recursively unneeded firmware dependencies.
if chroot "$root" /usr/bin/pacman -Q linux-aarch64 linux-firmware >/dev/null 2>&1; then
    chroot "$root" /usr/bin/pacman -Rns --noconfirm linux-aarch64 linux-firmware
fi
# QEMU user-mode cannot apply target-architecture seccomp filters to the host.
# This command-line override is build-only; it is not persisted in the image.
chroot "$root" /usr/bin/pacman --disable-sandbox -Syu --needed --noconfirm networkmanager wpa_supplicant bluez bluez-utils sudo python
chroot "$root" /usr/bin/pacman -Q > "$project/analysis/test-rootfs/packages.txt"
printf '%s\n' 'Package update completed in isolated ARM rootfs.'
