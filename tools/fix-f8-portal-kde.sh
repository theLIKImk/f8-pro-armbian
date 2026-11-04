#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
# Portal 后端 xdg-desktop-portal-kde 未运行 —— KDE 系统设置里的设备页和
# 应用权限弹窗依赖它。启动并设为自启：
systemctl --user unmask xdg-desktop-portal-kde 2>/dev/null
systemctl --user start xdg-desktop-portal-kde
sleep 3
systemctl --user is-active xdg-desktop-portal-kde
systemctl --user is-enabled xdg-desktop-portal-kde 2>&1
echo "--- 再看所有 portal 单元:"
systemctl --user list-units 'xdg-desktop-portal*' --no-legend
echo DONE
