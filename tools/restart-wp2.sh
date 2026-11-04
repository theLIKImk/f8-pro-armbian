#!/bin/sh
# UCM enable Mic 成功(rc=0)！但 WP 还没建 source —— WP 需要重新探测 card。
systemctl --user restart wireplumber
sleep 8
pactl list sources short
echo "--- card profiles now:"
pactl list cards | grep -E 'Active Profile' 
echo DONE
