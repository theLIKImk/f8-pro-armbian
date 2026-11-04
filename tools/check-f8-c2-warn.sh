#!/bin/sh
echo "=== 完整 Oops/告警内容 ==="
sudo -n dmesg | grep -B2 -A25 'end trace' | tail -40
echo DONE
