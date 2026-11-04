#!/bin/sh
sudo -n media-ctl -d /dev/media0 -p 2>/dev/null > /tmp/f8-m0.txt
grep -B2 -A3 'video1[1-4]' /tmp/f8-m0.txt | head -20
echo M1
grep 'entity' /tmp/f8-m0.txt | head -16
echo MARKER_DONE
