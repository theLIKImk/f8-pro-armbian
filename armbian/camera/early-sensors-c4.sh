# C4: root/dev/proc/sys/run have moved; PID1 is still the initramfs shell.
# Preserve the async waiting lists via cmdline, then meet CIF's 5-second
# notifier thread deadline by loading the existing official sensor modules.
echo 'F8 CAMERA C4 early sensor load begin' >/mnt/root/dev/kmsg 2>/dev/null || true
for camera_module in gc5035 ov8858; do
    if /bin/busybox timeout 8 /bin/busybox chroot /mnt/root /usr/sbin/modprobe "$camera_module"; then
        echo "F8 CAMERA C4 early loaded $camera_module" >/mnt/root/dev/kmsg 2>/dev/null || true
    else
        echo "F8 CAMERA C4 early load failed $camera_module; desktop service may retry" >/mnt/root/dev/kmsg 2>/dev/null || true
    fi
done
# No media unbind, capture or root configuration writes here.
