#!/bin/sh
sudo -n find /usr/share/alsa/ucm2 -path '*F8-PRO*' -o -name 'HiFi.conf' -path '*F8*' 2>/dev/null
echo "--- 全部 F8 相关 UCM:"
sudo -n find /usr/share/alsa/ucm2 -iname '*f8*' 2>/dev/null
echo "--- F8-PRO 目录内容:"
sudo -n ls -la /usr/share/alsa/ucm2/F8-PRO/ 2>/dev/null && cat /usr/share/alsa/ucm2/F8-PRO/HiFi.conf
echo DONE
