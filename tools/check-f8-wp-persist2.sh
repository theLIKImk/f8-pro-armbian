#!/bin/sh
# pactl 61% 与 ALSA 0dB 叠加导致实际 75%。音频默认策略应为单一层控制。
# 决定：ALSA 层固化硬件默认（asound.state 已固化 OUT2=0dB/PCM=166）。
# PipeWire 层默认应为 100% 透传，实际音量由用户经桌面调节；WP 已持久化 route 音量。
# 但 WP 记录的是旧值 0.097。把 sink 设为 100% 并让 WP 记住？
# 实际桌面体验：用户调音量走 WP；重启后 WP 恢复 route 音量。
# 检查 WP 持久化是否已写入当前 sink 音量：
pactl set-sink-volume alsa_output.platform-es8388-sound.HiFi__Speaker__sink 50%
sleep 5
grep 'output:analog-output-speaker' /home/f8test/.local/state/wireplumber/default-routes
echo "--- WP store check done. Current sink:"
pactl get-sink-volume alsa_output.platform-es8388-sound.HiFi__Speaker__sink | head -1
