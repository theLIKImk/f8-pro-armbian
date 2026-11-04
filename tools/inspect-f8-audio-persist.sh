#!/bin/sh
echo "=== WP default-routes content ==="
for f in /home/f8test/.local/state/wireplumber/default-routes/*; do echo "-- $f"; cat "$f"; echo; done
echo "=== WP default-nodes ==="
cat /home/f8test/.local/state/wireplumber/default-nodes/* 2>/dev/null | head -30
echo "=== alsa.state vs runtime diff (key controls) ==="
echo "--- saved Output2:"; grep -A2 "name 'Output 2 Playback Volume'" /var/lib/alsa/asound.state | grep value
echo "--- live Output2:"; amixer -c 0 sget 'Output 2' | grep -E 'Front (Left|Right):'
echo "--- saved PCM:"; grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep value
echo "--- live PCM:"; amixer -c 0 sget 'PCM' | grep Front
echo "--- saved Speaker sw:"; grep -A2 "name 'Speaker Switch'" /var/lib/alsa/asound.state | grep value
echo "--- live Speaker:"; amixer -c 0 sget 'Speaker' | grep Mono
echo "=== stored wp props (route/volume) ==="
ls -la /home/f8test/.local/state/wireplumber/
head -40 /home/f8test/.local/state/wireplumber/stream-properties/* 2>/dev/null
echo "=== DONE ==="
