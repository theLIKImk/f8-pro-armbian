#!/bin/sh
sudo -n media-ctl -d /dev/media0 -p 2>/dev/null > /tmp/f8-m0.txt
grep -n -iE 'gc5035|ov8858' /tmp/f8-m0.txt | head -6
echo "---all entities:"
grep 'entity' /tmp/f8-m0.txt | head -30
echo DONE
