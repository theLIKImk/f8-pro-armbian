#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
# KDE 系统设置/音频设置里的设备显示依赖 portal 与 PW 状态。检查当前完整状态：
echo "=== wpctl sources ==="
wpctl status 2>/dev/null | sed -n '/Sources/,/Filters/p' | head -8
echo "=== pactl sources ==="
timeout 8 pactl list sources short 2>&1
echo "=== xdg portal ==="
systemctl --user is-active xdg-desktop-portal xdg-desktop-portal-kde 2>&1
echo DONE
