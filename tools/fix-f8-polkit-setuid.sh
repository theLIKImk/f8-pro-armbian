#!/bin/sh
set -e
echo "=== 给 helper 加回 setuid root 位 ==="
ls -la /usr/lib/polkit-1/polkit-agent-helper-1
chmod u+s /usr/lib/polkit-1/polkit-agent-helper-1
ls -la /usr/lib/polkit-1/polkit-agent-helper-1
echo "=== 重启 polkit 与 agent 使其重新校验 ==="
systemctl restart polkit
echo DONE
