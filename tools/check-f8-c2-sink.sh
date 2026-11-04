#!/bin/sh
# "Async subdev notifier completed" —— CIF 的 async 链齐了！
# dphy1 的 pad0 (SINK) 应该接 sensor。上面输出里没显示 pad0 的连接 —— 看完整：
echo "== media0 全拓扑（找 sensor 实体）"
sudo -n media-ctl -d /dev/media0 -p 2>/dev/null | grep -B1 -A6 'pad0: SINK' | head -30
echo DONE
