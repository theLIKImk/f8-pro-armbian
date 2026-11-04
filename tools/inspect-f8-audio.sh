#!/bin/sh
echo "=== CARDS ==="
cat /proc/asound/cards 2>/dev/null
aplay -l 2>/dev/null
echo "=== ALSA STATE FILES ==="
ls -la /var/lib/alsa/ 2>/dev/null
head -50 /var/lib/alsa/asound.state 2>/dev/null
echo "=== PIPEWIRE ==="
systemctl is-active pipewire pipewire-pulse wireplumber 2>&1
echo "=== WIREPLUMBER CONFIG ==="
ls /etc/wireplumber/ 2>/dev/null
ls /home/f8test/.config/wireplumber/ 2>/dev/null
echo "=== UCM ==="
ls /usr/share/alsa/ucm2/conf.d/ 2>/dev/null | head
echo "=== MIXER CONTROLS ==="
amixer -c 0 scontrols 2>/dev/null
echo "=== KEY CONTROLS ==="
for c in "Speaker" "OUT2" "OUT1" "Headphone" "Playback" "Master" "DAC" "Route" "Mixer"; do
  amixer -c 0 sget "$c" 2>/dev/null | head -8
  echo "---"
done
echo "=== PACTL ==="
pactl info 2>/dev/null | head -8
pactl list sinks short 2>/dev/null
echo "=== DONE ==="
