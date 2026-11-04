#!/bin/sh
# Isolated test-root installation, not the live tablet or host root.
set -eu
base=/var/tmp/f8-pro-armbian
rootfs="$base/rootfs-trixie-evaluation"
test -f "$base/userspace-stage2.ok"
if [ "${F8_EVAL_PRIVATE_NS:-}" != 1 ]; then
    exec unshare --mount --propagation private env F8_EVAL_PRIVATE_NS=1 sh "$0"
fi
cleanup() {
    umount "$rootfs/proc" 2>/dev/null || true
}
trap cleanup EXIT HUP INT TERM
mount -t proc -o ro,nosuid,nodev,noexec proc "$rootfs/proc"
printf '#!/bin/sh\nexit 101\n' > "$rootfs/usr/sbin/policy-rc.d"
chmod 755 "$rootfs/usr/sbin/policy-rc.d"
chroot "$rootfs" apt-get -y --no-install-recommends install \
    systemd-sysv udev dbus kmod firmware-misc-nonfree > "$base/evaluation-core-install.log" 2>&1
test -x "$rootfs/usr/lib/systemd/systemd"
test -f "$rootfs/usr/lib/firmware/arm/mali/arch10.8/mali_csffw.bin"
printf 'F8-PRO development evaluation root; not a finished Armbian release\n' > "$rootfs/etc/f8-pro-evaluation"
touch "$base/evaluation-core.ok"
printf 'Minimal evaluation init + GPU firmware installed in isolated root only\n'
