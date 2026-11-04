sudo -n journalctl -k -b --no-pager -q 2>/dev/null | grep -E 'clear unready|Async registered|notifier|5-0037|5-0036|v4l2.*subdev.*(register|add)' | head -30
echo MARKER_DONE
