#!/bin/sh
# WP 文件 mtime 是 00:25:07（本次启动时写入），但值仍是 0.097 —— 说明 WP
# 持久化的是"route 音量"（device 层），而 pactl set-sink-volume 改的是 sink 软件音量。
# 两条通道不同。route 音量才跨重启生效。上一轮显示 oOut\c\sSpeaker 条目值 0.421875
# （对应 ALSA Output2=24 -9dB —— 与重启后硬件实测一致！）
# 验证：改 route 音量的正确方法 = 用 wpctl set-volume（device/route 层）
wpctl status 2>/dev/null | head -30
echo ---
wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null
echo DONE
