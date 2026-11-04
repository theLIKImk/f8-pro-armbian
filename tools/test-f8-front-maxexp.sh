#!/bin/sh
# 曝光 16 恒定 → 曝光没生效或帧全黑。试最大曝光 2020：
sudo -n v4l2-ctl -d /dev/v4l-subdev2 --set-ctrl exposure=2020 2>&1 | head -1
sleep 1
sudo -n timeout 15 v4l2-ctl -d /dev/video31 --set-fmt-video=width=640,height=480,pixelformat=NV12 \
  --stream-mmap=4 --stream-count=12 --stream-to=/tmp/f8-front-b.raw --stream-poll 2>&1 | tail -1
ls -la /tmp/f8-front-b.raw
echo MARKER_DONE
