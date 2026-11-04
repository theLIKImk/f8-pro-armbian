#!/bin/sh
sleep 25
grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep value
stat -c '%y' /var/lib/alsa/asound.state
systemctl is-active alsa-state
