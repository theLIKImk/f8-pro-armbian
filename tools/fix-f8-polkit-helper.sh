#!/bin/sh
set -e
echo "=== 备份并禁用 polkit-agent-helper.socket（回退 setuid helper，绕过 pidfd 依赖） ==="
systemctl stop polkit-agent-helper.socket 2>/dev/null || true
systemctl mask polkit-agent-helper.socket
systemctl mask polkit-agent-helper@.service 2>/dev/null || true
echo "=== 重启 polkitd 使其走 setuid fallback ==="
systemctl restart polkit
sleep 1
systemctl is-active polkit
systemctl is-enabled polkit-agent-helper.socket 2>&1
echo "=== 验证：以 f8test 发起一次真实 polkit 认证（timedate set-ntp，expect cancel/交互不崩） ==="
# 不自动输密码，只确认 helper 服务不再被 socket 激活路径调用
ls /run/systemd/units/ 2>/dev/null | grep -c polkit-agent-helper || true
echo DONE
