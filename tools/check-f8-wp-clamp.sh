#!/bin/sh
# 50% 设置后 pactl 读数仍 75%？可能 PipeWire 软件音量被设备 route 钳制。
# 检查设备节点（wireplumber 的 device 对象）音量：
pactl list sinks | grep -E 'Volume:|Mute:|Active Port' | head -6
echo ---devices
pactl list cards | grep -A6 'Volume:' | head -12
echo ---route-vol-in-wp-state
cat /home/f8test/.local/state/wireplumber/default-routes | head -6
echo DONE
