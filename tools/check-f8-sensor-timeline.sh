sudo -n journalctl -k -b -q --no-pager 2>/dev/null | awk '/gc5035 5-0037: driver version/,/rkisp0-vir0: rkisp driver/' | head -30
echo MARKER_DONE
