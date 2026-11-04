#!/bin/sh
echo "BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)"
uptime
echo "--- route volumes persisted:"
grep -E 'analog-output-speaker|oOut' /home/f8test/.local/state/wireplumber/default-routes
echo "--- device-layer volume:"
wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null || echo no-wpctl
echo "--- sink mute:"
pactl get-sink-mute alsa_output.platform-es8388-sound.HiFi__Speaker__sink
echo DONE
