#!/bin/sh
echo "=== ISP subdev pad0 (sink from sensor side) 链接状态 ==="
sudo -n media-ctl -d /dev/media2 -p 2>/dev/null | sed -n '/entity 1: rkisp-isp-subdev/,/entity 6/p' | head -20
echo "=== media3 同样 ==="
sudo -n media-ctl -d /dev/media3 -p 2>/dev/null | sed -n '/entity 1: rkisp-isp-subdev/,/entity 6/p' | head -20
echo DONE
