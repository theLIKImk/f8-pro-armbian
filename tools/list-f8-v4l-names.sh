#!/bin/sh
# sensor probe 成功、驱动检测到芯片。但 v4l-subdev 里没有 sensor —— 
# 有可能 sensor subdev 名不是 gc5035 开头？列出全部 44 个 video 节点名字：
for v in /sys/class/video4linux/*/; do
  echo "$(basename $v): $(cat $v/name 2>/dev/null)"
done
echo DONE
