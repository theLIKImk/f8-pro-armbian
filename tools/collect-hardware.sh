#!/bin/sh
# Read-only diagnostics for the original Linux system; no passwords or profiles.
# Run: sh collect-hardware.sh /tmp/f8-hardware
set -u
umask 077
out=${1:-/tmp/f8-hardware}
mode=${2:-all}
case "$mode" in all|system) ;; *) echo 'Mode must be all or system.' >&2; exit 2 ;; esac
if [ -e "$out" ]; then
    echo 'Output path already exists; select a new empty path.' >&2
    exit 1
fi
mkdir -p "$out" || exit 1
printf 'check\tstate\texit_code\n' >"$out/check-status.tsv"
run() {
    name=$1; shift
    if command -v "$1" >/dev/null 2>&1; then
        if command -v timeout >/dev/null 2>&1; then
            if timeout 40 "$@" >"$out/$name.txt" 2>&1; then rc=0; else rc=$?; fi
        else
            if "$@" >"$out/$name.txt" 2>&1; then rc=0; else rc=$?; fi
        fi
        printf '%s\tran\t%s\n' "$name" "$rc" >>"$out/check-status.tsv"
    else
        printf 'Tool unavailable: %s\n' "$1" >"$out/$name.txt"
        printf '%s\tunavailable\t127\n' "$name" >>"$out/check-status.tsv"
    fi
}
run kernel uname -a
run os-release cat /etc/os-release
printf 'XDG_SESSION_TYPE=%s\nDISPLAY=%s\nWAYLAND_DISPLAY=%s\n' "${XDG_SESSION_TYPE:-}" "${DISPLAY:-}" "${WAYLAND_DISPLAY:-}" >"$out/session-type.txt"
run ubuntu-graphics-packages dpkg-query -W '-f=${binary:Package}\t${Version}\t${db:Status-Status}\n' 'libmali*' 'libegl*' 'libgbm*' 'libgl*' 'mesa*' 'xserver-xorg*' 'rockchip*' 'camera-engine*' systemd
run board-model cat /sys/firmware/devicetree/base/model
run board-compatible cat /sys/firmware/devicetree/base/compatible
run bootargs cat /proc/cmdline
run memory cat /proc/meminfo
run devices ls -l /dev/dri /dev/mali0 /dev/video0 /dev/media0 /dev/input
run dmesg dmesg
run modules lsmod
run pci lspci -nnk
run usb lsusb
run block lsblk -o NAME,SIZE,TYPE,FSTYPE,PARTUUID,MOUNTPOINT
run block-bytes lsblk -b -o NAME,SIZE,TYPE,FSTYPE,PARTUUID,MOUNTPOINT
run input cat /proc/bus/input/devices
run alsa-cards cat /proc/asound/cards
run alsa-playback aplay -l
run alsa-capture arecord -l
run alsa-mixer amixer contents
run cameras v4l2-ctl --list-devices
run media media-ctl -p
run bluetooth bluetoothctl list
run bluetooth-uarts ls -l /dev/ttyS8 /dev/ttyS9
run wifi-driver-paths cat /sys/module/bcmdhd/parameters/firmware_path /sys/module/bcmdhd/parameters/nvram_path
run rfkill rfkill list
run network nmcli -f DEVICE,TYPE,STATE device status
run rotation gdbus call --system --dest net.hadess.SensorProxy --object-path /net/hadess/SensorProxy --method org.freedesktop.DBus.Properties.GetAll net.hadess.SensorProxy
run system-services systemctl --failed --no-pager
if [ "$mode" = all ] && [ "$(id -u)" -ne 0 ]; then
    run pipewire wpctl status
    run pulseaudio pactl info
    run audio-routes pactl list short sinks
    run renderer-gl glxinfo -B
    run renderer-egl eglinfo
    run renderer-vulkan vulkaninfo --summary
    run display-x11 xrandr --verbose
    run display-wayland kscreen-doctor -o
    run user-services systemctl --user --failed --no-pager
    run kwin qdbus6 org.kde.KWin /KWin supportInformation
    run kwin-qt5 qdbus org.kde.KWin /KWin supportInformation
else
    printf 'Desktop checks skipped for root/system collection; run the desktop launcher as the logged-in user.\n' >"$out/desktop-checks-skipped.txt"
fi
run graphics-journal journalctl -b --no-pager -k
for root in /sys/bus/iio/devices /sys/class/power_supply /sys/class/backlight /sys/class/thermal; do
    [ -d "$root" ] || continue
    find -L "$root" -maxdepth 2 -type f \( -name name -o -name type -o -name capacity -o -name status -o -name temp -o -name brightness -o -name max_brightness -o -name '*_raw' -o -name '*_scale' -o -name '*mount_matrix' \) -print 2>/dev/null |
    while IFS= read -r f; do
        printf '\n%s\n' "$f"
        cat "$f" 2>/dev/null || true
    done >>"$out/sysfs.txt"
done
for log in /var/log/Xorg.0.log "$HOME/.local/share/xorg/Xorg.0.log"; do
    if [ -r "$log" ]; then
        printf '\n%s\n' "$log" >>"$out/xorg-logs.txt"
        cat "$log" >>"$out/xorg-logs.txt"
    fi
done
if [ -r /sys/firmware/fdt ]; then
    cp /sys/firmware/fdt "$out/live.dtb"
fi
printf 'Diagnostics saved to %s\n' "$out"
printf 'Run as the logged-in desktop user for renderer checks; root may be needed for kernel logs.\n'
