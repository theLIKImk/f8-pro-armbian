#!/bin/sh
echo "=== ALSA-RESTORE LOG ==="
journalctl -u alsa-restore -b --no-pager -q 2>&1 | tail -5
echo "=== state-daemon conf ==="
cat /etc/alsa/state-daemon.conf 2>/dev/null || echo no-state-daemon-conf
echo "=== sink volume/mute ==="
pactl get-sink-volume alsa_output.platform-es8388-sound.HiFi__Speaker__sink 2>/dev/null
pactl get-sink-mute alsa_output.platform-es8388-sound.HiFi__Speaker__sink 2>/dev/null
echo "=== card profile ==="
pactl list cards short 2>/dev/null
echo "=== DONE ==="
