#!/bin/sh
echo "BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)"
echo "=== pending async 现状 ==="
sudo -n cat /sys/kernel/debug/v4l2-async/pending_async_subdevices 2>/dev/null | head -20
echo "=== camera-start 服务状态 ==="
systemctl is-active f8-camera-start.service
echo "=== 预览状态 ==="
cat /run/user/1601/f8-camera-preview-status.json 2>/dev/null | head -5
echo MARKER_DONE
