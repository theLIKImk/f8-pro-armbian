#!/bin/sh
# Trial PID1 handoff with original Arch as a read-only container, all writes in RAM.
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
umask 077
fail() {
    echo "F8 R4 INIT STOP: $*" >/dev/kmsg 2>/dev/null || true
    if [ -f /run/f8/eval-logs.img ]; then
        /bin/sh /f8-evaluation-report init-failed || true
    fi
    while :; do sleep 60; done
}
mkdir -p /dev /proc /sys /run
mount -t devtmpfs devtmpfs /dev || fail devtmpfs
mount -t proc proc /proc || fail proc
mount -t sysfs sysfs /sys || fail sysfs
mount -t tmpfs -o mode=0755,nosuid tmpfs /run || fail tmpfs
mkdir -p /run/f8/container /run/f8/lower /run/f8-overlay/upper /run/f8-overlay/work /mnt/root
cp /f8-firstboot-logs.img /run/f8/eval-logs.img || fail ram-log-image
exec >/run/f8/evaluation-steps.log 2>&1
echo 'F8 R4 RAM-overlay init reached'
[ "$(uname -r)" = '6.1.172-f8-pro-armbian-eval' ] || fail release
case " $(cat /proc/cmdline) " in *' systemd.gpt_auto=0 '*) ;; *) fail gpt-auto-policy;; esac
attempt=0
while [ ! -b /dev/mmcblk0p6 ] && [ "$attempt" -lt 30 ]; do sleep 1; attempt=$((attempt+1)); done
[ -b /dev/mmcblk0p6 ] || fail container-missing
[ "$(blkid -s PARTUUID -o value /dev/mmcblk0p6)" = '614e0000-0000-4b53-8000-1d28000054a9' ] || fail partuuid
mount -t ext4 -o ro,noload /dev/mmcblk0p6 /run/f8/container || fail readonly-container
[ -f /run/f8/container/etc/arch-release ] || fail container-identity
image=/run/f8/container/var/lib/f8-pro/armbian-evaluation/rootfs.squashfs
[ -f "$image" ] && [ ! -L "$image" ] || fail image-missing
echo 'a69fdacdc7ad5fc1d9239ffb271c40bb2e05fb151e0635c2f59b2ef70885a8dc  /run/f8/container/var/lib/f8-pro/armbian-evaluation/rootfs.squashfs' | sha256sum -c - || fail image-sha256
mount -t squashfs -o ro,loop "$image" /run/f8/lower || fail squashfs
[ -f /run/f8/lower/etc/f8-pro-evaluation ] || fail marker
[ -x /run/f8/lower/usr/lib/systemd/systemd ] || fail systemd
[ -s /run/f8/lower/usr/lib/modules/6.1.172-f8-pro-armbian-eval/modules.dep ] || fail module-release
mount -t overlay overlay -o lowerdir=/run/f8/lower,upperdir=/run/f8-overlay/upper,workdir=/run/f8-overlay/work /mnt/root || fail overlay
mkdir -p /mnt/root/etc/systemd/system /mnt/root/usr/libexec/f8-pro
for unit in /f8-eval-units/*; do cp "$unit" /mnt/root/etc/systemd/system/ || fail unit-copy; done
cp /f8-evaluation-report /mnt/root/usr/libexec/f8-pro/evaluation-report || fail report-copy
echo 'Verified lower image, original Arch ro,noload; target upper/work are RAM'
moved=
for fs in dev proc sys run; do
    mkdir -p "/mnt/root/$fs"
    if ! mount --move "/$fs" "/mnt/root/$fs"; then
        for prior in $moved; do mount --move "/mnt/root/$prior" "/$prior" || true; done
        fail "move-$fs"
    fi
    moved="$fs $moved"
done
cd /mnt/root || fail chdir
exec switch_root /mnt/root /usr/lib/systemd/systemd --unit=f8-evaluation.target --log-level=info
