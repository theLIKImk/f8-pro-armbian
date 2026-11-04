#!/bin/sh
sleep 5
systemctl --user is-active wireplumber pipewire
pactl list sources short 2>&1
echo DONE
