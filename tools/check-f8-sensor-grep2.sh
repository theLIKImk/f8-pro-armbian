sudo -n grep -E 'gc5035|ov8858|detected' /tmp/f8-dmesg-full.txt
echo M1
sudo -n sed -n '1,2p' /tmp/f8-dmesg-full.txt
echo MARKER_DONE
