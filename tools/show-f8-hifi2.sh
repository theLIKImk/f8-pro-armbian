#!/bin/sh
sudo -n grep -c "Main Mic" /usr/share/alsa/ucm2/F8-PRO/HiFi.conf
sudo -n cat /usr/share/alsa/ucm2/F8-PRO/HiFi.conf | tail -25
echo DONE
