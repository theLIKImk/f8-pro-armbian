#!/bin/sh
# alsactl restore 顺序问题：'spk switch' 由 codec 驱动的 DAPM 或 PipeWire 复位。
# A3 验证播放时 Speaker/OUT2 on、spk switch on。让最终 asound.state = 播放验证时的组合。
amixer -c 0 sset 'Speaker' on
amixer -c 0 sset 'OUT2' on
amixer -c 0 sset 'OUT1' off
amixer -c 0 sset 'Headphone' off
amixer -c 0 sset 'spk switch' on
amixer -c 0 sset 'hp switch' off
amixer -c 0 sset 'Left Mixer Left' on
amixer -c 0 sset 'Right Mixer Right' on
amixer -c 0 sset 'Output 2' 30
amixer -c 0 sset 'Output 1' 30
amixer -c 0 sset 'PCM' 166
alsactl store 0 2>&1 | head -1
echo "--- final state file:"
grep -A2 "name 'Speaker Switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'spk switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'OUT2 Switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'OUT1 Switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'Headphone Switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'hp switch'" /var/lib/alsa/asound.state | grep value
grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep 'value\.'
grep -A2 "name 'Output 2 Playback Volume'" /var/lib/alsa/asound.state | grep value
stat -c '%y' /var/lib/alsa/asound.state
echo DONE
