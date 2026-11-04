#!/bin/sh
# video0 存在（刚才 -d /dev/video0 打不开？重试直出）：
echo "=== CIF lvds2 (前摄) video11 or video0 试帧 ==="
# video0 属于 rkcif-mipi-lvds (disabled)？video11 属于 lvds2？确认归属：
sudo -n v4l2-ctl -d /dev/video11 --list-formats-ext 2>&1 | head -6
echo "---"
sudo -n v4l2-ctl -d /dev/video0 --list-formats-ext 2>&1 | head -6
echo DONE
