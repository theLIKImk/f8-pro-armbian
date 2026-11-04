#!/bin/sh
# C2 已启动（用户已刷入），双 sensor 都绑定。现在核对完整 media 链：
# 关键是 sensor 实体是否链接进 CIF。用 media-ctl 看完整拓扑中 gc5035/ov8858：
for m in /dev/media0 /dev/media1; do
  echo "== $m"
  sudo -n media-ctl -d "$m" -p 2>/dev/null | grep -iE 'gc5035|ov8858|mipi|dphy' | head -10
done
echo "=== sensor subdev entities in media2/3 ==="
for m in /dev/media2 /dev/media3; do
  echo "== $m"
  sudo -n media-ctl -d "$m" -p 2>/dev/null | grep -iE 'gc5035|ov8858' | head -5
done
echo "=== dmesg sensor links ==="
sudo -n dmesg | grep -iE 'gc5035|ov8858|rkcif.*link|dphy.*link' | tail -12
echo DONE
