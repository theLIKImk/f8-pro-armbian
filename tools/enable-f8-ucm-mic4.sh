#!/bin/sh
# alsaucm open 需要用 card 名。先 open by number:
sudo -n alsaucm open 0
sudo -n alsaucm set _verb HiFi
sudo -n alsaucm set _enadev Mic
echo "rc=$?"
sleep 2
pactl list sources short
echo DONE
