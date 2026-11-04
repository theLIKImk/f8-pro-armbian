#!/bin/sh
# 验证 alsactl rdaemon 的实际保存行为：改音量，触发 save
amixer -c 0 sset 'PCM' 160 >/dev/null 2>&1
sleep 3
/usr/sbin/alsactl -E HOME=/run/alsa -E XDG_RUNTIME_DIR=/run/alsa/runtime save 0 2>&1 || echo manual-save-failed
grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep 'value\.'
amixer -c 0 sset 'PCM' 166 >/dev/null 2>&1
/usr/sbin/alsactl -E HOME=/run/alsa -E XDG_RUNTIME_DIR=/run/alsa/runtime save 0 2>&1 || true
grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep 'value\.'
stat -c '%y' /var/lib/alsa/asound.state
echo DONE
