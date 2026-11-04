#!/bin/sh
# Candidate RAM-overlay trial boot. Offline packaging does not establish board support.
# The existing Arch partition is only a read-only container for a checked image.
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
umask 077
fail() {
    echo "F8 Armbian evaluation stopped: $*" >/dev/kmsg 2>/dev/null || true
    while :; do sleep 60; done
}
# Adapted from the bridge helper; compare the filesystem field, not "nodev".
fs_available() {
    [ -n "${1:-}" ] || return 1
    while read -r _fs_kind _fs_name; do
        [ "${_fs_name:-$_fs_kind}" = "$1" ] && return 0
    done < /proc/filesystems
    return 1
}
ensure_fs() {
    [ -n "${1:-}" ] || return 1
    fs_available "$1" && return 0
    modprobe "$1" || return 1
    fs_available "$1"
}
mkdir -p /dev /proc /sys /run
mount -t devtmpfs devtmpfs /dev || fail 'devtmpfs'
mount -t proc proc /proc || fail 'proc'
mount -t sysfs sysfs /sys || fail 'sysfs'
mount -t tmpfs -o mode=0755,nosuid tmpfs /run || fail 'tmpfs'
mkdir -p /run/f8/container /run/f8/lower /mnt/root
case " $(cat /proc/cmdline) " in
    *' systemd.gpt_auto=0 '*) ;;
    *) fail 'automatic GPT discovery must be disabled' ;;
esac
# Modules are packaged for precisely one kernel ABI, never borrowed from another.
[ "$(uname -r)" = "$(cat /etc/f8-evaluation.release)" ] || fail 'kernel release mismatch'
ensure_fs squashfs || fail 'SquashFS unavailable'
ensure_fs overlay || fail 'overlay unavailable'
attempt=0
while [ ! -b /dev/mmcblk0p6 ] && [ "$attempt" -lt 30 ]; do
    sleep 1
    attempt=$((attempt + 1))
done
[ -b /dev/mmcblk0p6 ] || fail 'container partition missing'
[ "$(blkid -s PARTUUID -o value /dev/mmcblk0p6)" = '614e0000-0000-4b53-8000-1d28000054a9' ] || fail 'container PARTUUID mismatch'
mount -t ext4 -o ro,noload /dev/mmcblk0p6 /run/f8/container || fail 'read-only container'
[ -f /run/f8/container/etc/arch-release ] || fail 'unexpected container identity'
image=/run/f8/container/var/lib/f8-pro/armbian-evaluation/rootfs.squashfs
[ -f "$image" ] && [ ! -L "$image" ] || fail 'evaluation image missing'
# Packager must provide this checksum after the final SquashFS has been built.
[ -s /etc/f8-evaluation.sha256 ] || fail 'packaged checksum missing'
cd /run/f8/container/var/lib/f8-pro/armbian-evaluation || fail 'image directory'
sha256sum -c /etc/f8-evaluation.sha256 || fail 'image checksum'
mount -t squashfs -o ro,loop rootfs.squashfs /run/f8/lower || fail 'SquashFS'
[ -f /run/f8/lower/etc/f8-pro-evaluation ] || fail 'evaluation marker missing'
[ -x /run/f8/lower/usr/lib/systemd/systemd ] || fail 'systemd missing'
[ -s "/run/f8/lower/usr/lib/modules/$(uname -r)/modules.dep" ] || fail 'rootfs module release mismatch'
mkdir -p /run/f8-overlay/upper /run/f8-overlay/work
mount -t overlay overlay -o lowerdir=/run/f8/lower,upperdir=/run/f8-overlay/upper,workdir=/run/f8-overlay/work /mnt/root || fail 'RAM overlay'
# This script never rewrites machine identity, credentials or the container FS.
for fs in dev proc sys run; do
    mkdir -p "/mnt/root/$fs"
    mount --move "/$fs" "/mnt/root/$fs" || fail "move $fs"
done
cd /mnt/root || fail 'new root directory'
exec switch_root /mnt/root /usr/lib/systemd/systemd --log-level=info
