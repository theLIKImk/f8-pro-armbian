sudo -n cat /tmp/f8-full.txt | grep -vE 'apparmor|audit' | head -50
echo MARKER_DONE
