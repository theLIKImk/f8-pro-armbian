#!/bin/sh
# 检查 amixer sset 是否真的生效（前面 set 160 疑似未生效，live 仍是 166）
amixer -c 0 sset 'PCM' 150 2>&1 | tail -2
echo "--- live after set 150:"
amixer -c 0 sget 'PCM' | grep 'Front Left'
sleep 1
echo "--- rdaemon running?"; ps aux | grep -v grep | grep -c alsactl
echo "--- try store while daemon active:"
alsactl store 0 2>&1 | head -1
grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep 'value\.'
