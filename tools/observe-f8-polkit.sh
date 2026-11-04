#!/bin/sh
echo "=== polkit state ==="
systemctl is-active polkit
systemctl is-enabled polkit-agent-helper.socket 2>&1 || true
echo "=== 现在请你在平板上再试一次改日期：会弹密码框，输入 f8test 密码 ==="
echo "=== 我这边持续观察 journal 60 秒 ==="
sudo -n timeout 60 journalctl -f --no-pager 2>/dev/null | grep --line-buffered -iE 'polkit|timedate' | head -25
echo OBSERVE_DONE
