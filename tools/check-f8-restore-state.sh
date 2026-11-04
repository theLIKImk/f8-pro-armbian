#!/bin/sh
echo "BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)"
echo "--- alsa-restore:"
systemctl is-enabled alsa-restore
systemctl status alsa-restore --no-pager -n 3 2>&1 | head -8
echo "--- journal:"
journalctl -u alsa-restore -b --no-pager -q 2>&1 | tail -4
echo "--- asound.state key values (what will be restored next boot):"
grep -A2 "name 'Output 2 Playback Volume'" /var/lib/alsa/asound.state | grep value
grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep 'value\.'
grep -A2 "name 'Speaker Switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'OUT2 Switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'OUT1 Switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'Headphone Switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'spk switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'hp switch'" /var/lib/alsa/asound.state | grep value
echo DONE
