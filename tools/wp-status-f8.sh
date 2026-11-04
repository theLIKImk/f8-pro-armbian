#!/bin/sh
# WP 文件未再写。可能持久化策略：只在 route (device port) 变化时写。
# wpctl set-volume 0.61 设置的是 sink 软件音量而非 route 音量。
# route 音量 = 设备端口音量。设置 route 音量的正确方式：
#   wpctl set-volume <device-id> 0.61  （对设备节点，不是 @DEFAULT_AUDIO_SINK@）
wpctl status 2>/dev/null | sed -n '/Audio/,/Video/p' | head -25
