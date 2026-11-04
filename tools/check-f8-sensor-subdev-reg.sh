sudo -n journalctl -k -b --no-pager -q 2>/dev/null | grep -E '5-0037|5-0036' | grep -viE 'supply|Looking|version|lane|pixel|detected|Detected|dep|power' | head -15
echo M1
sudo -n journalctl -k -b --no-pager -q 2>/dev/null | grep -iE 'v4l2.*(register|async)|async.*(wait|complete)' | head -10
echo MARKER_DONE
