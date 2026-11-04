#!/bin/sh
# PCM 控件可能被 PipeWire 接管（其会把 PCM 写回自身目标值）
echo "--- pipewire/wireplumber running:"
ps aux | grep -v grep | grep -cE 'pipewire|wireplumber'
echo "--- pactl sink volume (PipeWire layer):"
pactl get-sink-volume alsa_output.platform-es8388-sound.HiFi__Speaker__sink
echo "--- set sink volume via pactl to 60pct then check PCM:"
pactl set-sink-volume alsa_output.platform-es8388-sound.HiFi__Speaker__sink 60%
sleep 1
amixer -c 0 sget 'PCM' | grep 'Front Left'
echo "--- set 55pct:"
pactl set-sink-volume alsa_output.platform-es8388-sound.HiFi__Speaker__sink 55%
sleep 1
amixer -c 0 sget 'PCM' | grep 'Front Left'
echo "--- restore 50pct default:"
pactl set-sink-volume alsa_output.platform-es8388-sound.HiFi__Speaker__sink 50%
sleep 1
amixer -c 0 sget 'PCM' | grep 'Front Left'
echo DONE
