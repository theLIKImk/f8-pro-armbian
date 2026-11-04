#!/bin/sh
# source 仍未出现。可能 UCM verb 需要先 enable Mic。用 alsaucm 启用：
sudo -n alsaucm -c 0 open HiFi 2>&1 | head -2
sudo -n alsaucm -c 0 _verb HiFi 2>&1 | head -2
sudo -n alsaucm -c 0 _enadev Mic 2>&1 | head -2
sleep 3
pactl list sources short
echo "--- 若无, WP 日志:"
journalctl --user -u wireplumber -b --no-pager -q 2>/dev/null | tail -8
echo DONE
