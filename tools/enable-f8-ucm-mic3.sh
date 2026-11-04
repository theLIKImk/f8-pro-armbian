#!/bin/sh
# alsaucm 的 open 流程：open card -> set _verb -> set _enadev
sudo -n alsaucm -c 0 open HiFi
sudo -n alsaucm -c 0 set _verb HiFi
sudo -n alsaucm -c 0 set _enadev Mic
echo "rc=$?"
sleep 3
pactl list sources short
echo DONE
