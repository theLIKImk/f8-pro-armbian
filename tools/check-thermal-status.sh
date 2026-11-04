set -eu
printf 'TEMPERATURES\n'
for f in /sys/class/thermal/thermal_zone*/temp; do printf '%s=' "$f"; cat "$f"; done
printf 'TRIPS\n'
for f in /sys/class/thermal/thermal_zone0/trip_point_*; do printf '%s=' "$f"; cat "$f"; done
printf 'BUILD PROCESSES\n'
pgrep -a -x makepkg || true
pgrep -a -x cc1plus || true
printf 'SYSTEM\n'
systemctl is-system-running
