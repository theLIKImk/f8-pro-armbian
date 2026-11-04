#!/bin/sh
echo "=== polkit agent processes ==="
ps aux | grep -v grep | grep -iE 'polkit' || echo no-polkit-agent
echo "=== polkit service ==="
systemctl status polkit --no-pager -n 3 2>&1 | head -8
echo "=== user groups ==="
id
echo "=== polkit rules ==="
ls /etc/polkit-1/rules.d/ /usr/share/polkit-1/rules.d/ 2>/dev/null
cat /etc/polkit-1/rules.d/*.rules 2>/dev/null
echo "=== recent polkit/auth journal errors ==="
journalctl -b --no-pager -q 2>/dev/null | grep -iE 'polkit|authentication agent|pkttyagent' | tail -15
echo "=== session env ==="
systemctl --user is-active plasma-plasmashell 2>/dev/null
echo "XDG_SESSION_TYPE=$XDG_SESSION_TYPE"
echo "=== journal agent crash ==="
journalctl --user -b --no-pager -q 2>/dev/null | grep -iE 'polkit.*agent|agent.*polkit' | tail -10
echo DONE
