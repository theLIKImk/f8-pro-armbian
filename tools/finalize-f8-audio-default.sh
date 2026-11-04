#!/bin/sh
# 将 asound.state 修正为目标默认（PCM=166），因守护期间曾把 156/161 写入。
# 桌面实际音量将由 WirePlumber route 音量控制，ALSA 层 PCM 保持 166 基线。
amixer -c 0 sset 'PCM' 166 >/dev/null 2>&1
/usr/sbin/alsactl store 0 2>&1 | head -1
grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep 'value\.'
grep -A2 "name 'Output 2 Playback Volume'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'spk switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'hp switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'Speaker Switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'Headphone Switch'" /var/lib/alsa/asound.state | grep value
echo "--- confirm restore path condition now passes:"
ls /etc/alsa/state-daemon.conf 2>&1
echo DONE
