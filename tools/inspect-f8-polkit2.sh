#!/bin/sh
echo "=== agent env ==="
tr '\0' '\n' < /proc/1400/environ 2>/dev/null | grep -E 'DISPLAY|WAYLAND|XDG_SESSION|XDG_RUNTIME' 
echo "=== journal around authorization attempts ==="
sudo -n journalctl -b --no-pager 2>/dev/null | grep -iE 'polkit|polkitd' | tail -20
echo "=== user journal ==="
journalctl --user -b --no-pager 2>/dev/null | grep -iE 'polkit|auth' | tail -10
echo "=== agent unit/launcher ==="
ls /etc/xdg/autostart/org.kde.polkit-kde-authentication-agent-1.desktop 2>/dev/null && grep -E 'Exec|Wayland|OnlyShowIn' /etc/xdg/autostart/org.kde.polkit-kde-authentication-agent-1.desktop
echo "=== test polkit action from CLI ==="
timeout 5 pkttyagent 2>&1 | head -2 &
sleep 1
echo DONE
