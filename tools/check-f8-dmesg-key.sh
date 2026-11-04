sudo -n grep -c '' /tmp/f8-full.txt
echo M1
sudo -n awk '/fead0000|gc5035|ov8858|csi2-dphy|rkcif-mipi-lvds2: Async|notifier/{print}' /tmp/f8-full.txt | head -20
echo MARKER_DONE
