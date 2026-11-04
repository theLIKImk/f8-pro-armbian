#!/bin/sh
# video0 不存在（设备号可能被 sditf 模式吞了）。全部 CIF stream 节点：
for v in /dev/video*; do
  n=$(cat /sys/class/video4linux/$(basename $v)/name 2>/dev/null)
  echo "$v: $n"
done | grep -E 'stream_cif|scale_ch|tools_id' | head -12
echo "---"
# "get remote terminal sensor failed" 是关键 —— CIF 找不到 sensor 端点。
# 因为 sensor subdev 没注册进 media 图（之前发现 v4l-subdev 里没有 gc5035/ov8858）。
# 确认：sensor 驱动是否实现了 v4l2_subdev_ops 且注册成功 —— 看 /dev/v4l-subdev* 权限和
# driver 的 async register 时间点（可能在 CIF notifier 完成之后注册但没匹配上）。
sudo -n dmesg | grep -iE 'v4l2.*async|async.*register|subdev.*register|registered.*subdev' | tail -8
echo DONE
