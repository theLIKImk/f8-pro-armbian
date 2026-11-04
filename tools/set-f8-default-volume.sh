#!/bin/sh
# 最终策略：默认音量经 PipeWire 层管理。恢复 sink 61%（对应我们固化的 166）？
# 不：目标默认 = WP 记录的 route 音量。WP default-routes 已存 channelVolumes 0.097/0.125。
# 我们选择统一默认：sink 61% (-13dB, PCM=166)，并让 WP 持久化该 route 音量。
pactl set-sink-volume alsa_output.platform-es8388-sound.HiFi__Speaker__sink 61%
sleep 1
pactl get-sink-volume alsa_output.platform-es8388-sound.HiFi__Speaker__sink | head -1
amixer -c 0 sget 'PCM' | grep 'Front Left'
echo "--- wait for WP to persist route volumes (default-routes file mtime):"
stat -c '%y' /home/f8test/.local/state/wireplumber/default-routes
sleep 3
stat -c '%y' /home/f8test/.local/state/wireplumber/default-routes
grep 'output:analog-output-speaker' /home/f8test/.local/state/wireplumber/default-routes
echo DONE
