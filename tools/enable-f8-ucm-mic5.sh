#!/bin/sh
# alsaucm 需要 card 的 UCM 名。查 /sys 类里 UCM manager 名称：
cat /proc/asound/card0/id
sudo -n alsaucm open rockchipes8388c 2>&1 | head -2
sudo -n alsaucm set _verb HiFi 2>&1 | head -2
sudo -n alsaucm set _enadev Mic 2>&1 | head -2
sleep 2
pactl list sources short
echo DONE
