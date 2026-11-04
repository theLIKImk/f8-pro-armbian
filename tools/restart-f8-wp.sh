#!/bin/sh
# UCM 已识别 Mic 设备。重启 WirePlumber 让它重新探测 card，创建 source：
systemctl --user restart pipewire wireplumber
sleep 6
pactl list sources short
echo DONE
