#!/bin/sh
echo "=== 修复后的认证尝试日志 ==="
sudo -n journalctl --since '-10 min' --no-pager -q 2>/dev/null | grep -iE 'polkit|timedate|authenticat' | tail -30
echo DONE
