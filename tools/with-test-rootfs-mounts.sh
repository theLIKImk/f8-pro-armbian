#!/bin/bash
# Temporary private mounts for offline chroot checks; no host block devices.
set -euo pipefail
root=/var/tmp/f8-pro-archlinux-20261027/rootfs-vendor-staging
if [ "${F8_VERIFY_MOUNT_NS:-}" != 1 ]; then
    exec unshare --mount --propagation private env F8_VERIFY_MOUNT_NS=1 bash "$0" "$@"
fi
[ "$(id -u)" -eq 0 ] && [ -f "$root/etc/arch-release" ] && [ "$#" -gt 0 ]
cleanup() {
    umount -R "$root/dev" 2>/dev/null || true
    umount "$root/proc" 2>/dev/null || true
    umount "$root" 2>/dev/null || true
}
trap cleanup EXIT
mount --bind "$root" "$root"
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
"$@"
