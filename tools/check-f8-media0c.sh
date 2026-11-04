#!/bin/sh
sudo -n media-ctl -d /dev/media0 -p 2>/dev/null > /tmp/f8-m0.txt
grep -B4 'device node name' /tmp/f8-m0.txt | grep -E 'entity|device node' | head -24
echo MARKER_DONE
