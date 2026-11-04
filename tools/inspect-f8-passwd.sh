#!/bin/sh
echo "=== /etc/shadow 与 passwd 状态 ==="
sudo -n ls -la /etc/shadow /etc/passwd /etc/shadow-
sudo -n lsattr /etc/shadow /etc/passwd 2>/dev/null
echo "=== 根分区是否只读 ==="
findmnt -o TARGET,SOURCE,OPTIONS / | tail -1
echo "=== PAM passwd 栈 ==="
grep -v '^#' /etc/pam.d/passwd | grep -v '^$'
echo "=== 最近尝试日志 ==="
sudo -n journalctl --since '-10 min' --no-pager -q 2>/dev/null | grep -iE 'passwd|shadow|chauthtok' | tail -10
echo "=== 磁盘空间 ==="
df -h / | tail -1
echo DONE
