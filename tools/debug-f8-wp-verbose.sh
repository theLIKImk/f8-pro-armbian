#!/bin/sh
# WirePlumber pid 801 —— 这是重启前旧的？看它什么时候起的。另查 WP 配置里
# 是否禁用了 UCM capture 或者 monitor。更关键：让 WP 详细日志打 UCM 探测：
systemctl --user stop wireplumber
Gaub=1 PIPEWIRE_DEBUG=4 timeout 12 /usr/bin/wireplumber 2>&1 | grep -iE 'ucm|profile.*hifi|capture|source|mic' | head -30
echo "=== restart service ==="
systemctl --user start wireplumber
sleep 4
pactl list sources short
echo DONE
