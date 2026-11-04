#!/bin/sh
echo "=== 最近 5 分钟 polkit 相关 journal ==="
sudo -n journalctl --since '-30 min' --no-pager -q 2>/dev/null | grep -iE 'polkit|timedate|authenticat' | tail -25
echo DONE
