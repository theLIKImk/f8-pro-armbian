#!/bin/sh
# F8-PRO 音频默认路由固化脚本（通过 sudo 执行，可回退）
set -e
TS=$(date -u +%Y%m%dT%H%M%SZ)
BK="/var/lib/alsa/asound.state.pre-audio-default-$TS"
echo "=== 1. 备份现有 asound.state ==="
cp -a /var/lib/alsa/asound.state "$BK"
ls -la "$BK"
echo "=== 2. 应用默认路由/开关/音量（基于 A3 已验证播放路由） ==="
# 路由：输出到 OUT2（扬声器），关闭 OUT1/Headphone；spk on, hp off
amixer -c 0 sset 'Speaker' on >/dev/null
amixer -c 0 sset 'OUT2' on >/dev/null
amixer -c 0 sset 'OUT1' off >/dev/null
amixer -c 0 sset 'Headphone' off >/dev/null
amixer -c 0 sset 'spk switch' on >/dev/null
amixer -c 0 sset 'hp switch' off >/dev/null
# 混音矩阵：PCM 接入左右输出混音器
amixer -c 0 sset 'Left Mixer Left' on >/dev/null
amixer -c 0 sset 'Right Mixer Right' on >/dev/null
amixer -c 0 sset 'Left Mixer Left Bypass' off >/dev/null
amixer -c 0 sset 'Right Mixer Right Bypass' off >/dev/null
# 音量：OUT2 = 0dB(30/33)，PCM = -6dB(约166/192) 作为安全默认
amixer -c 0 sset 'Output 2' 30 >/dev/null
amixer -c 0 sset 'Output 1' 30 >/dev/null
amixer -c 0 sset 'PCM' 166 >/dev/null
echo "=== 3. 写入持久化状态 ==="
/usr/sbin/alsactl -E HOME=/run/alsa store 0
ls -la /var/lib/alsa/asound.state
echo "=== 4. 校验写入的关键控制项 ==="
grep -A2 "name 'Output 2 Playback Volume'" /var/lib/alsa/asound.state | grep value
grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep 'value\.'
grep -A2 "name 'spk switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'hp switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'Speaker Switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'OUT2 Switch'" /var/lib/alsa/asound.state | grep value
echo "=== 5. WirePlumber 用户级默认（sink 已是默认 Speaker，route 已记录） ==="
cat /home/f8test/.local/state/wireplumber/default-nodes
echo "=== DONE ==="
