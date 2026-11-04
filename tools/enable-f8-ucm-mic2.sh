#!/bin/sh
# alsaucm 语法不对。alsaucm set _verb HiFi / set _enadev Mic:
sudo -n alsaucm -c 0 set _verb HiFi 2>&1 | head -2
sudo -n alsaucm -c 0 set _enadev Mic 2>&1 | head -2
echo "rc=$?"
sleep 3
pactl list sources short
echo "--- 确认 UCM 当前状态:"
sudo -n alsaucm -c 0 get _verb 2>&1
echo DONE
