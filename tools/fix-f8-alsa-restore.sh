#!/bin/sh
# 修复：删除 state-daemon.conf，恢复 alsa-restore 开机恢复路径
# （rdaemon 模式实测不轮询保存也无益处；ala-restore 是 Ubuntu/Armbian 的标准恢复机制）
rm -f /etc/alsa/state-daemon.conf
systemctl stop alsa-state 2>/dev/null || true
systemctl start alsa-restore
sleep 1
systemctl is-active alsa-restore
echo "--- after manual restore, live values:"
amixer -c 0 sget 'Speaker' | grep Mono
amixer -c 0 sget 'OUT2' | grep Mono
amixer -c 0 sget 'spk switch' | grep Mono
amixer -c 0 sget 'hp switch' | grep Mono
amixer -c 0 sget 'Output 2' | grep 'Front Left'
amixer -c 0 sget 'PCM' | grep 'Front Left'
echo "--- journal:"
journalctl -u alsa-restore -b --no-pager -q | tail -2
echo DONE
