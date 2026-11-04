#!/bin/sh
# open 'rockchip,es8388-codec' 没报错了（open 成功）。但 set _enadev 失败可能因为
# 每个 alsaucm 调用是独立进程，open 的状态不保留！需要单进程内连续命令：
sudo -n alsaucm -b - <<'EOF'
open rockchip,es8388-codec
set _verb HiFi
set _enadev Mic
EOF
echo "rc=$?"
sleep 2
pactl list sources short
echo DONE
