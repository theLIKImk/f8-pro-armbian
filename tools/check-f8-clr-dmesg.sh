#!/bin/sh
echo "=== 触发后 dmesg ==="
sudo -n dmesg | tail -15
echo MARKER_DONE
