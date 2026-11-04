sudo -n dmesg | head -100 > /tmp/f8-boot-head.txt
sudo -n grep -nE 'gc5035|ov8858|sensor|camera|i2c@fead' /tmp/f8-boot-head.txt
echo M1
sudo -n awk '/i2c@fead|fead0000/{print NR": "$0}' /tmp/f8-dmesg-full.txt | head -5
echo MARKER_DONE
