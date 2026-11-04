sudo -n dmesg > /tmp/f8-full.txt 2>/dev/null
sudo -n grep -vE 'apparmor|audit' /tmp/f8-full.txt | sed -n '1,80p'
echo MARKER_DONE
