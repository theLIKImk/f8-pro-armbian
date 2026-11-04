#!/bin/sh
# 系统没装 xdg-desktop-portal-kde，用的 GTK 后端。KDE 系统设置音频模块
# 其实直接读 PipeWire，不需要 portal-kde。检查 KCM 是否能列出设备——
# 模拟 plasmashell 视角查 sources 完整属性（设备名/端口）：
export XDG_RUNTIME_DIR=/run/user/1601
timeout 8 pactl list sources 2>&1 | grep -E 'Name:|Description:|Active Port:|Mute:' | head -10
echo "=== 检查 kglobalaccel/plasmashell 音频小程序依赖是否正常 ==="
plasma-viewport 2>/dev/null; true
echo DONE
