#!/bin/sh
# 固化麦克风捕获默认配置到 asound.state
amixer -c 0 sset 'Left Channel' 8 >/dev/null
amixer -c 0 sset 'Right Channel' 8 >/dev/null
amixer -c 0 sset 'ALC Capture Function' Stereo >/dev/null
amixer -c 0 sset 'ALC Capture Max PGA' 7 >/dev/null
amixer -c 0 sset 'ALC Capture Min PGA' 0 >/dev/null
amixer -c 0 sset 'Capture Digital' 192 >/dev/null
amixer -c 0 sset 'Capture Mute' off >/dev/null
amixer -c 0 sset 'Main Mic' on >/dev/null
amixer -c 0 sset 'Headset Mic' off >/dev/null
amixer -c 0 sset 'ADC Data Select' 'Left Right' >/dev/null
amixer -c 0 sset 'Left PGA Mux' 'DifferentialL' >/dev/null
amixer -c 0 sset 'Right PGA Mux' 'DifferentialR' >/dev/null
sudo -n /usr/sbin/alsactl store 0 2>/dev/null || sudo -n /usr/sbin/alsactl store 0 -f /var/lib/alsa/asound.state
echo "=== 校验固化 ==="
sudo -n grep -A2 "name 'Left Channel Capture Volume'" /var/lib/alsa/asound.state | grep value
sudo -n grep -A2 "name 'Right Channel Capture Volume'" /var/lib/alsa/asound.state | grep value
echo "=== PipeWire source 出现了吗 ==="
pactl list sources short
echo DONE
