#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
# 主 conf 用 spa-json 段式。正确覆写方式应是同段名覆盖。查 wireplumber.conf 里
# monitor.alsa 的 properties 段:
grep -B2 -A8 '^monitor.alsa' /usr/share/wireplumber/wireplumber.conf | head -30
echo "---"
# 关键词：api.alsa.use-acp 默认 true？全局搜:
grep -rn 'use-acp\|use-ucm' /usr/share/wireplumber/ 2>/dev/null | head
echo DONE
