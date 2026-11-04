#!/bin/sh
# Install only into a new isolated desktop root. Keep the verified minimal root.
set -eu
base=/var/tmp/f8-pro-armbian
project=/mnt/d/Netdisk/Other/F8-PRO/archlinux
rootfs="$base/rootfs-trixie-wayland"
core="$base/rootfs-trixie-evaluation"
reports="$project/analysis/armbian/userspace"
exec 9>"$base/wayland-install.lock"
flock -n 9 || { echo 'Wayland root installation already running' >&2; exit 1; }
test -f "$base/evaluation-core.ok"
for path in "$core/proc" "$core/sys" "$core/dev"; do
    ! mountpoint -q "$path"
done
if [ ! -e "$rootfs" ]; then
    mkdir "$rootfs"
    cp -a --reflink=auto "$core/." "$rootfs/"
    touch "$base/wayland-root-cloned.ok"
fi
test -f "$base/wayland-root-cloned.ok"
if [ "${F8_WAYLAND_PRIVATE_NS:-}" != 1 ]; then
    # Release this invocation's flock before the namespace child acquires it.
    flock -u 9
    exec unshare --mount --propagation private env F8_WAYLAND_PRIVATE_NS=1 sh "$0"
fi
mkdir -p "$reports"
cleanup() {
    umount "$rootfs/proc" 2>/dev/null || true
    for name in wayland-install-update wayland-install-simulation wayland-install; do
        if [ -f "$base/$name.log" ]; then cp "$base/$name.log" "$reports/"; fi
    done
}
trap cleanup EXIT HUP INT TERM
mount -t proc -o ro,nosuid,nodev,noexec proc "$rootfs/proc"
printf '#!/bin/sh\nexit 101\n' > "$rootfs/usr/sbin/policy-rc.d"
chmod 755 "$rootfs/usr/sbin/policy-rc.d"
tr -d '\r' < "$project/armbian/wayland-packages.txt" | sed '/^#/d; /^[[:space:]]*$/d' \
    > "$base/wayland-install-packages.txt"
chroot "$rootfs" apt-get update > "$base/wayland-install-update.log" 2>&1
# All entries are package names maintained in this repository, not shell code.
packages=$(cat "$base/wayland-install-packages.txt")
# Intentional word splitting of the validated package names.
if LC_ALL=C grep -Eqv '^[a-z0-9][a-z0-9+.-]*(:arm64)?$' "$base/wayland-install-packages.txt"; then
    echo 'Invalid package list' >&2
    exit 1
fi
chroot "$rootfs" apt-get -s --no-install-recommends install $packages \
    > "$base/wayland-install-simulation.log" 2>&1
! grep -Eq '^Inst (kwin-x11|grub[^ ]*|linux-image[^ ]*|u-boot[^ ]*) ' "$base/wayland-install-simulation.log"
date -u +%FT%TZ > "$reports/wayland-install.started"
set +e
chroot "$rootfs" env DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends install $packages \
    > "$base/wayland-install.log" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$reports/wayland-install.exit"
date -u +%FT%TZ > "$reports/wayland-install.finished"
[ "$status" -eq 0 ] || exit "$status"
chroot "$rootfs" dpkg-query -W > "$reports/wayland-installed-packages.tsv"
test -x "$rootfs/usr/bin/kwin_wayland"
test -x "$rootfs/usr/bin/startplasma-wayland"
test -x "$rootfs/usr/bin/sddm"
test -x "$rootfs/usr/bin/maliit-keyboard"
! chroot "$rootfs" dpkg-query -W -f='${db:Status-Status}\n' kwin-x11 2>/dev/null | grep -qx installed
touch "$base/wayland-packages-installed.ok"
printf 'Wayland packages installed only in isolated root; no compositor or services started\n'
