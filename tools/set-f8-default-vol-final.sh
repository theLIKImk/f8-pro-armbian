#!/bin/sh
# 设备层(route)音量当前 0.61 正是之前 pactl set 的 61%，WP 已记住。
# 为保证这是持久的默认（而非仅 sink 软件层），用 wpctl 明确设置一次并确认写盘：
wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.61
sleep 8
stat -c '%y' /home/f8test/.local/state/wireplumber/default-routes
grep 'oOut' /home/f8test/.local/state/wireplumber/default-routes
wpctl get-volume @DEFAULT_AUDIO_SINK@
echo DONE
