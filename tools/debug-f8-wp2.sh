#!/bin/sh
# 换个更直接的思路：UCM 只是让 WP 创建 source 的一种方式；WirePlumber 也支持
# 无 UCM 的简单 profile（基于 PCM capabilities 的 "HiFi" 需要设备定义）。
# 但更快的路径：检查 WP 的 monitor API 会给 capture PCM 建 node 的条件 —— 
# api.alsa.soft-mixer 等。直接看 WP 设备对象上的 profile 列表：
wpctl status 2>/dev/null | sed -n '/Devices/,/Sinks/p'
echo "---"
# 也看 UCM verb 是否需要每次 boot enable；重启后 UCM 状态掉了吗（rc=0 刚才是设置过的）：
sudo -n cat /proc/asound/card0/ucm 2>/dev/null || echo no-ucm-proc
echo DONE
