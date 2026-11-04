sudo -n journalctl -k -b --no-pager -q 2>/dev/null | head -60 | grep -vE 'apparmor|audit'
echo MARKER_DONE
