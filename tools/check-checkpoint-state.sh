set -eu
printf 'SYSTEM\n'
systemctl is-system-running
printf 'FAILED UNITS\n'
systemctl --failed --no-legend --no-pager
printf 'TEST PROCESSES\n'
for name in kwin_wayland weston makepkg cc1plus; do pgrep -a -x "$name" || true; done
printf 'TEST UNITS\n'
systemctl list-units --all 'f8-wayland-*' --no-legend --no-pager
printf 'ACTIVE VT\n'
cat /sys/class/tty/tty0/active
printf 'ROOT FS\n'
df -h /
