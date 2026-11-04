set -eu
printf '\nBUILD LOG\n'
tail -n 12 /home/alarm/f8-pro-builds/layer-shell-qt-6.7.5-gTPkBGDM/build.log
printf '\nSYSTEM\n'
systemctl is-system-running
printf '\nTEMPERATURE MILLIDEGREES\n'
for node in /sys/class/thermal/thermal_zone*/temp; do cat "$node"; done
