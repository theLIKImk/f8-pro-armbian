#!/bin/sh
sudo -n ls /proc/device-tree/ | grep -iE 'csi|dphy|lvds|mipi'
echo DONE
