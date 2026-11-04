#!/bin/sh
# WP 未即时写盘（周期性/事件驱动）。手动触发保存：wpctl 没有显式 save；
# WirePlumber 在音量改变事件后延迟写。再等并检查；若仍不写，改用 wpctl status 确认
# route 对象 0.61 已在会话内，持久化文件随事件最终写入。等待 20s：
sleep 20
stat -c '%y' /home/f8test/.local/state/wireplumber/default-routes
grep 'oOut' /home/f8test/.local/state/wireplumber/default-routes
echo DONE
