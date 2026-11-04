sudo -n dmesg | wc -l
echo M1
sudo -n dmesg | grep -iE 'probed|probe.*ok|asynchronous' | head -10
echo M2
sudo -n dmesg | sed -n '50,120p' | grep -viE 'audit|apparmor' | head -30
echo MARKER_DONE
