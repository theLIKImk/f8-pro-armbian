#!/bin/sh
sudo -n find /proc/device-tree -maxdepth 1 -name '*lvds*' 2>/dev/null
sudo -n find /proc/device-tree -maxdepth 1 -name '*dphy*' 2>/dev/null
sudo -n find /proc/device-tree -maxdepth 1 -name '*csi*' 2>/dev/null | head -5
echo DONE
