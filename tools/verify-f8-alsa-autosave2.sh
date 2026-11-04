#!/bin/sh
# 触发一次真实音量变化并等守护自动保存（-n 19 秒周期）
amixer -c 0 sset 'PCM' 160 >/dev/null 2>&1
sleep 21
echo "--- after PCM->160, wait 21s:"
grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep 'value\.'
amixer -c 0 sset 'PCM' 166 >/dev/null 2>&1
sleep 21
echo "--- after PCM->166, wait 21s:"
grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep 'value\.'
stat -c '%y' /var/lib/alsa/asound.state
echo DONE
