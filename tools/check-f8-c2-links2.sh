#!/bin/sh
echo "== media0"
sudo -n media-ctl -d /dev/media0 -p 2>/dev/null | grep -iE 'gc5035|ov8858|dphy' | head -8
echo "== media1"
sudo -n media-ctl -d /dev/media1 -p 2>/dev/null | grep -iE 'gc5035|ov8858|dphy' | head -8
echo "== dmesg links"
sudo -n dmesg | grep -iE 'gc5035|ov8858' | tail -8
echo DONE
