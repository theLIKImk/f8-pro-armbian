#!/bin/sh
# C4 下前摄 CIF 直出（路线A实测）：video0（lvds2 stream_cif_mipi_id0）
# GC5035 subdev = v4l-subdev2，曝光固定
sudo -n v4l2-ctl -d /dev/v4l-subdev2 --set-ctrl exposure=1200 2>/dev/null
echo "=== set fmt RG10 2592x1944 on video0 ==="
sudo -n v4l2-ctl -d /dev/video0 --set-fmt-video=width=2592,height=1944,pixelformat=RG10 2>&1 | head -2
echo "=== stream 2 frames ==="
sudo -n timeout 20 v4l2-ctl -d /dev/video0 --stream-mmap=4 --stream-count=2 --stream-to=/tmp/f8-front-rg10.raw --stream-poll 2>&1 | tail -1
ls -la /tmp/f8-front-rg10.raw 2>/dev/null
echo MARKER_DONE
