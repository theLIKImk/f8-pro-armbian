#!/bin/sh
# rdaemon 不轮询。它应在退出(关闭)时保存。验证停服务是否会保存当前值。
amixer -c 0 sset 'PCM' 160 >/dev/null 2>&1
echo "--- live now:"; amixer -c 0 sget 'PCM' | grep 'Front Left'
systemctl stop alsa-state
sleep 1
echo "--- state file after stop (expect save_and_quit wrote 160):"
grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep 'value\.'
# 恢复默认并再存
systemctl start alsa-state
amixer -c 0 sset 'PCM' 166 >/dev/null 2>&1
alsactl store 0 2>&1 | head -1
echo "--- final:"
grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep 'value\.'
stat -c '%y' /var/lib/alsa/asound.state
echo DONE
