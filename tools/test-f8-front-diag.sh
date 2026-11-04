#!/bin/sh
# Y 恒定 16 = 全黑。曝光控制无效或 sensor 没出数据（ISP 输出的是固定色）。
# 对照：C4 验收时前摄 ISP 12 帧成功（通过 v4l2-ctl stream），用的命令是什么？
# 先验证 sensor 本体出流（CIF 直出 RAW 曾成功 2 帧）：
echo "=== sensor exposure readback ==="
sudo -n v4l2-ctl -d /dev/v4l-subdev2 --get-ctrl=exposure 2>&1 | head -2
echo "=== 试 video22（rkisp0，后摄链）对照 —— 确认 ISP 输出机制本身正常 ==="
sudo -n timeout 8 v4l2-ctl -d /dev/video22 --set-fmt-video=width=640,height=480,pixelformat=NV12 \
  --stream-mmap=4 --stream-count=4 --stream-to=/tmp/f8-rear-now.raw --stream-poll 2>&1 | tail -1
ls -la /tmp/f8-rear-now.raw 2>/dev/null
echo MARKER_DONE
