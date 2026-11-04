sudo -n journalctl -k -b -q --no-pager 2>/dev/null | grep -E 'gc5035|ov8858' | grep -viE 'supply|Looking|version|lane|pixel|detected|Detected|Fixed dep' | head -12
echo MARKER_DONE
