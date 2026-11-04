#!/bin/sh
# 关键缺口确认：44 个节点里没有 gc5035/ov8858 的 v4l-subdev —— sensor subdev
# 没有注册到任何 media 图。这就是 C1→C2 的核心遗留问题：sensor→dphy pad0 的
# 链接不存在（media0 中 dphy1 pad0: SINK,MUST_CONNECT 无任何 -> 指向它）。
# 查内核里 sensor 驱动的 async 注册器是否完成（v4l2_async 等 sensor):
sudo -n dmesg | grep -iE 'v4l2|async|notifier' | grep -viE 'rkcif|rkisp|csi2' | tail -10
echo "---sensor 驱动 probe 是否注册了 subdev（driver version 行后有没有报错）:"
sudo -n dmesg | sed -n '/gc5035 5-0037: driver version/,+6p'
echo DONE
