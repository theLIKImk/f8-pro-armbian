#!/bin/sh
# 结论：sink 音量由 WirePlumber route 音量（device 层）钳制；软件 50% 映射到硬件 PCM。
# 最终默认策略：
#  - ALSA asound.state：OUT2=on 0dB(30)、OUT1/HP off、spk on、PCM=166 —— 已固化并经 alsa-restore 开机恢复。
#  - WirePlumber：default-nodes 已固化默认 sink=Speaker；route 音量由 WP 自动持久化到
#    ~/.local/state/wireplumber/default-routes（当前 0.097 与 0.422 两条历史记录）。
# 统一桌面默认：sink route 音量 = 50%。请用户在桌面用音量键确认听感后由 WP 自动记住。
# 现在只验证 alsa-restore 的开机恢复路径确实存在且将被调用：
systemctl is-enabled alsa-restore
systemctl cat alsa-restore | grep -E 'ExecStart|After|Wanted'
echo DONE
