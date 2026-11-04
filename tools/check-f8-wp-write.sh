#!/bin/sh
# set-sink-volume 后 WP 文件没更新？检查 sink 实际值与文件差异，等待更久（WP 周期性写）
pactl get-sink-volume alsa_output.platform-es8388-sound.HiFi__Speaker__sink | head -1
sleep 12
stat -c '%y' /home/f8test/.local/state/wireplumber/default-routes
grep -c channelVolumes /home/f8test/.local/state/wireplumber/default-routes
grep 'analog-output-speaker' /home/f8test/.local/state/wireplumber/default-routes
echo "--- sink now:"
pactl get-sink-volume alsa_output.platform-es8388-sound.HiFi__Speaker__sink | head -1
echo DONE
