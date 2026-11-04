#!/bin/sh
echo "=== polkit 认证成功的记录（最近10分钟） ==="
sudo -n journalctl --since '-10 min' --no-pager -q 2>/dev/null | grep -iE 'polkit.*authenticate|polkitd' | tail -8
echo "=== 有密码的账户（shadow 第二字段非 * / !） ==="
sudo -n awk -F: '$2 !~ /^[!*]/ {print $1}' /etc/shadow
echo DONE
