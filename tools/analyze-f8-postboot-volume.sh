#!/bin/sh
# 分析重启后：OUT2 on ✓、spk switch on ✓、Speaker on ✓、hp off ✓
# 但 Output 2=24 / PCM=152 —— 不是 30/166。alsactl restore 应该恢复了 30/166。
# 恢复后 WirePlumber/PipeWire 启动时又把 route 音量(0.097→24？)写回硬件。
# 这正是"桌面默认音量由 WP 控制"的表现。检查 WP route 音量文件当前值：
grep 'output:analog-output-speaker' /home/f8test/.local/state/wireplumber/default-routes
grep '\\\\oOut' /home/f8test/.local/state/wireplumber/default-routes
echo "--- alsactl restore did run:"
journalctl -u alsa-restore -b --no-pager -q | tail -2
echo "--- 时序：WP 启动晚于 alsa-restore，WP 把持久化的 route 音量写硬件 = 桌面音量持久化生效"
echo "--- 目标默认音量调整方式：改 WP route 音量一次，WP 会记住并在每次启动写回"
pactl set-sink-volume alsa_output.platform-es8388-sound.HiFi__Speaker__sink 61%
sleep 5
grep 'output:analog-output-speaker' /home/f8test/.local/state/wireplumber/default-routes
echo DONE
