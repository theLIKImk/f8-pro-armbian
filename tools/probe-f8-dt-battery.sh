#!/bin/sh
sudo -n find /proc/device-tree -iname '*battery*' 2>/dev/null
echo "---i2c6 节点子项:"
sudo -n ls /proc/device-tree/i2c@fec90000/ 2>/dev/null || sudo -n ls /proc/device-tree/ | grep -i i2c
echo DONE
