#!/bin/sh
sudo -n find /proc/device-tree/csi2-dphy1/ -type d | head -10
echo "---"
sudo -n ls /proc/device-tree/csi2-dphy1/ports/ 2>/dev/null || echo no-ports-dir
echo DONE
