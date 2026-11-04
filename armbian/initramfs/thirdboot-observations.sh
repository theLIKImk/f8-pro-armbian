# R3 only: verify original Arch userspace without starting PID1 or services.
echo 'READONLY ORIGINAL ROOT PROBE; NO SERVICES OR JOURNAL REPLAY' >/run/logdisk/ROOTPROBE.TXT
mkdir -p /run/original-root
root_uuid=$(/sbin/blkid -s PARTUUID -o value /dev/mmcblk0p6)
if [ "$root_uuid" = '614e0000-0000-4b53-8000-1d28000054a9' ]; then
    if mount -t ext4 -o ro,noload /dev/mmcblk0p6 /run/original-root; then
        cat /proc/mounts >/run/logdisk/MOUNTS.TXT
        if [ -f /run/original-root/etc/arch-release ]; then
            cat /run/original-root/etc/os-release >>/run/logdisk/ROOTPROBE.TXT
            timeout 10 chroot /run/original-root /usr/bin/true >/run/logdisk/RUNTRUE.TXT 2>&1
            echo "exit_code=$?" >>/run/logdisk/RUNTRUE.TXT
            timeout 10 chroot /run/original-root /usr/lib/systemd/systemd --version >/run/logdisk/RUNSYS.TXT 2>&1
            echo "exit_code=$?" >>/run/logdisk/RUNSYS.TXT
        else
            echo 'Arch identity missing; no binaries executed' >>/run/logdisk/ROOTPROBE.TXT
        fi
        umount /run/original-root || echo 'Readonly unmount failed' >>/run/logdisk/ROOTPROBE.TXT
    else
        echo 'Readonly mount failed' >>/run/logdisk/ROOTPROBE.TXT
    fi
else
    echo 'PARTUUID mismatch or unavailable; no mount attempted' >>/run/logdisk/ROOTPROBE.TXT
fi
cat /sys/class/tty/console/active >/run/logdisk/CONSOLE.TXT 2>&1
cat /sys/devices/system/cpu/possible >/run/logdisk/CPUPOSS.TXT
echo 'F8 R3 SMP AND READONLY USERSPACE SNAPSHOT COMPLETE' >/dev/kmsg
