#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
# WP 正常但无节点输出可能 pw-cli 挂了。用 pipewire 原生方式：直接创建 capture
# 测试不依赖 WP source —— 如果内核 capture 能录（已证明能），剩下的问题只是 WP 不建 node。
# 检查 alsa monitor 是否被 monitor.alsa.properties 配置段语法错误弄挂了 UCM 探测：
WP_TEST=$(cat /usr/share/wireplumber/wireplumber.conf.d/50-f8-ucm.conf)
echo "$WP_TEST"
# WirePlumber 1.6 语法：monitor.alsa.properties 应该是 "monitor.alsa.properties = {...}"
# 但也可能要在 wireplumber.conf 的 monitor.alsa 段。看主 conf:
grep -A5 'monitor.alsa' /usr/share/wireplumber/wireplumber.conf | head -20
echo DONE
