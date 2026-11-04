#!/bin/sh
# Read-only system diagnostics; writes only a new private report directory.
# Run on the tablet: sudo sh collect-arch-firstboot.sh
set -eu
umask 077
[ "$(id -u)" -eq 0 ] || { echo 'Run with sudo on the tablet.' >&2; exit 2; }
[ -r /etc/arch-release ] || { echo 'Not an Arch system; stopping.' >&2; exit 2; }
command -v timeout >/dev/null 2>&1 || { echo 'timeout is required.' >&2; exit 2; }
compatible=/sys/firmware/devicetree/base/compatible
if ! tr '\000' '\n' < "$compatible" | grep -qx 'rockchip,rk3588s-tablet-f12-v11'; then
    echo 'Unexpected board; stopping.' >&2
    exit 2
fi
out=$(mktemp -d /tmp/f8-arch-firstboot-XXXXXXXX)
printf 'check\texit_code\n' > "$out/check-status.tsv"
run() {
    name=$1
    shift
    if timeout 30 "$@" > "$out/$name.txt" 2>&1; then rc=0; else rc=$?; fi
    printf '%s\t%s\n' "$name" "$rc" >> "$out/check-status.tsv"
}
run identity sh -c 'cat /proc/sys/kernel/hostname; cat /etc/os-release; uname -a; cat /proc/cmdline'
run board sh -c 'tr "\000" "\n" < /sys/firmware/devicetree/base/compatible'
run failed-units systemctl --failed --no-pager
run boot-timing systemd-analyze
run services systemctl status --no-pager --full sshd NetworkManager systemd-resolved f8-pro-wifi f8-pro-bluetooth bluetooth f8-pro-keyring
run boot-journal journalctl -b --no-pager -n 1500
run kernel-journal journalctl -b -k --no-pager -n 1500
run service-journal journalctl -b --no-pager -n 1000 -u sshd -u NetworkManager -u systemd-resolved -u f8-pro-wifi -u f8-pro-bluetooth -u bluetooth -u f8-pro-keyring
run network-devices nmcli -f DEVICE,TYPE,STATE device status
run addresses ip -brief address
run routes ip route show
run dns resolvectl status
run rfkill rfkill list
run modules lsmod
run wifi-module modinfo bcmdhd_pcie
run bluetooth bluetoothctl list
run storage lsblk -b -o NAME,SIZE,TYPE,FSTYPE,PARTUUID,MOUNTPOINT
run mounts findmnt --real
run packages pacman -Q
run devices sh -c 'ls -l /dev/dri /dev/mali0 /dev/ttyS9; cat /proc/asound/cards; cat /proc/bus/input/devices'
run ssh-policy sshd -T
printf 'REPORT=%s\n' "$out"
printf 'Private report may contain SSIDs, MAC addresses and device identifiers. Do not publish raw logs.\n'
# No connection profiles, private keys, process environments or password files.
# No service restarts, package changes, audio recording or camera capture.
exit 0
