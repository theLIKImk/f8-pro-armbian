#!/bin/sh
# 两个 sensor 都被 DPHY 检测到了！链路：
# media0: dphy1 ← (ENABLED)，media1: dphy2 ← ENABLED。
# 但 sensor 实体名没直接出现在 grep —— sensor 链是 sensor→dphy→cif。
# 看 dphy 的 sink 端接什么（0号 pad 是 sink）：
echo "== media0 dphy1 详情"
sudo -n media-ctl -d /dev/media0 -p 2>/dev/null | sed -n '/entity 58/,/^$/p' | head -12
echo "== media1 dphy2 详情"
sudo -n media-ctl -d /dev/media1 -p 2>/dev/null | sed -n '/entity 58/,/^$/p' | head -12
echo "== dmesg 完整链路注册（async subdev）=="
sudo -n dmesg | grep -iE 'rkcif.*async|dphy.*async|async.*bound|linked' | tail -8
echo DONE
