#!/bin/sh
pactl set-sink-volume alsa_output.platform-es8388-sound.HiFi__Speaker__sink 50%
sleep 2
pactl get-sink-volume alsa_output.platform-es8388-sound.HiFi__Speaker__sink | head -1
amixer -c 0 sget PCM | grep 'Front Left'
echo DONE
