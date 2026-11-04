#!/bin/sh
echo "BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)"
uptime
systemctl is-system-running
echo "--- alsa-restore active:"; systemctl is-active alsa-restore
echo "--- live key controls after reboot:"
amixer -c 0 sget 'Speaker' | grep Mono
amixer -c 0 sget 'OUT2' | grep Mono
amixer -c 0 sget 'OUT1' | grep Mono
amixer -c 0 sget 'Headphone' | grep Mono
amixer -c 0 sget 'spk switch' | grep Mono
amixer -c 0 sget 'hp switch' | grep Mono
amixer -c 0 sget 'PCM' | grep 'Front Left'
amixer -c 0 sget 'Output 2' | grep 'Front Left'
echo "--- pipewire sink:"
pactl list sinks short
pactl get-sink-mute alsa_output.platform-es8388-sound.HiFi__Speaker__sink
echo DONE
