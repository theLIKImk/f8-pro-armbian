#!/bin/sh
echo "=== create state-daemon.conf ==="
printf 'SAVE_STATE=true\n' > /etc/alsa/state-daemon.conf
cat /etc/alsa/state-daemon.conf
systemctl start alsa-state 2>&1 || true
sleep 2
systemctl is-active alsa-state
ps aux | grep -v grep | grep alsactl | head -3
echo "=== change PCM then check autosave (~20s) ==="
amixer -c 0 sset 'PCM' 165 >/dev/null 2>&1
sleep 21
grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep 'value\.'
echo "=== restore PCM 166 ==="
amixer -c 0 sset 'PCM' 166 >/dev/null 2>&1
echo "=== DONE ==="
