sudo -n journalctl -k -b -q --no-pager 2>/dev/null | grep 'rkcif rkcif-mipi-lvds2' | grep -v 'update sensor' | head -10
echo MARKER_DONE
