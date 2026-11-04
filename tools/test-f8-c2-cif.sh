#!/bin/sh
# select timeout = sensor 没出流。RKISP 路径需要从 CIF stream 节点入（非 rawrd），
# 或 sensor subdev 需要 s_power/s_stream。CIF 的 stream_cif_mipi_id0 才是原始路径。
# rkisp SDITF 方案：CIF→sditf→ISP。CIF stream 节点 streamon 时 sensor 才会开流。
# ISP mainpath 直接 streamon 不触发 CIF/sensor 流启动。
# 正确顺序：先 streamon CIF 原始流节点（stream_cif_mipi_id0, video0/video11）或
# 让 sditf 链路工作。先试 CIF 直出路径（不经过 ISP）：
echo "=== CIF raw stream: video0 (stream_cif_mipi_id0 of lvds2/前摄?) ==="
sudo -n v4l2-ctl -d /dev/video0 --set-fmt-video=width=1152,height=864,pixelformat=NV12 2>&1 | head -2
sudo -n timeout 10 v4l2-ctl -d /dev/video0 --stream-mmap=4 --stream-count=1 --stream-to=/tmp/f8-cif0.raw --stream-poll 2>&1
echo "rc=$?"
ls -la /tmp/f8-cif0.raw 2>/dev/null
echo "=== dmesg ==="
sudo -n dmesg | grep -iE 'rkcif|gc5035|ov8858' | grep -viE 'apparmor|dummy|Looking' | tail -8
echo DONE
