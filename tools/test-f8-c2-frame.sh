#!/bin/sh
# 有界短时取帧验证：对两个 ISP mainpath 分别试抓 1 帧。
# 使用 v4l2-ctl --stream-mmap 有界抓取，不热重绑，不写无限数据。
# ISP0 mainpath = video22, ISP1 mainpath = video31（按 media 图确认过）
echo "== 节点确认 =="
cat /sys/class/video4linux/video22/name
cat /sys/class/video4linux/video31/name
echo "== video22 (rkisp0 mainpath) 5秒试帧 =="
sudo -n timeout 6 v4l2-ctl -d /dev/video22 --stream-mmap=4 --stream-count=1 --stream-to=/tmp/f8-isp0.raw --stream-poll 2>&1 | tail -3
ls -la /tmp/f8-isp0.raw 2>/dev/null && rm -f /tmp/f8-isp0.raw
echo "== video31 (rkisp1 mainpath) 5秒试帧 =="
sudo -n timeout 6 v4l2-ctl -d /dev/video31 --stream-mmap=4 --stream-count=1 --stream-to=/tmp/f8-isp1.raw --stream-poll 2>&1 | tail -3
ls -la /tmp/f8-isp1.raw 2>/dev/null && rm -f /tmp/f8-isp1.raw
echo "== dmesg 新增 =="
sudo -n dmesg | tail -8
echo DONE
