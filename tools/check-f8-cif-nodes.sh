grep -H . /sys/class/video4linux/*/name | grep stream_cif
echo M1
# C4 时前摄 CIF 直出节点从 dmesg 找（当时记录 RG10 2592x1944 2帧成功）
sudo -n journalctl -k -b -q --no-pager 2>/dev/null | grep -iE 'rkcif.*stream|cif_mipi' | head -5
echo MARKER_DONE
