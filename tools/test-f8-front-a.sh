#!/bin/sh
# 前摄路线A实测：固定曝光 v4l2 直出 12 帧（对照 C4 前摄验收参数：blanking 80 已持久化）
# gc5035 subdev = v4l-subdev2；exposure 默认 1984（约14fps场景）
echo "=== set sensor exposure (fixed, 保守室内值) ==="
sudo -n v4l2-ctl -d /dev/v4l-subdev2 --set-ctrl exposure=1200 2>&1
echo "=== stream 12 frames NV12 640x480 from video31 ==="
sudo -n timeout 15 v4l2-ctl -d /dev/video31 --set-fmt-video=width=640,height=480,pixelformat=NV12 \
  --stream-mmap=4 --stream-count=12 --stream-to=/tmp/f8-front-a.raw --stream-poll 2>&1
echo "rc=$?"
ls -la /tmp/f8-front-a.raw 2>/dev/null
echo MARKER_DONE
