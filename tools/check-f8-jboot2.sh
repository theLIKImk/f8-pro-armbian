sudo -n journalctl -k -b --no-pager -q 2>/dev/null | grep -E 'gc5035|ov8858|csi2-dphy|rkcif-mipi-lvds2|Async' | head -25
echo MARKER_DONE
