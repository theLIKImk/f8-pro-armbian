set -eu
printf 'KWIN\n'
tail -n 3 /home/alarm/f8-pro-builds/kwin-6.7.5-v73ibK4G/build.log
printf 'ACTIVITY MANAGER\n'
tail -n 3 /home/alarm/f8-pro-builds/kactivitymanagerd-6.7.5-sZW8PHsH/build.log
printf 'CPU\n'
getconf _NPROCESSORS_ONLN
for f in /sys/class/thermal/thermal_zone*/temp; do printf '%s=' "$f"; cat "$f"; done
printf 'MAKEPKG\n'
pgrep -a -x makepkg || true
printf 'TIMEOUT PROCESSES\n'
ps -eo pid,ppid,args | grep 'timeout --signal=TERM' | grep -v grep || true
