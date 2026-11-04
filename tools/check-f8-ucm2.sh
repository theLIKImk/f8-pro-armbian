#!/bin/sh
# 找到了：UCM rockchip_es8388 存在！查看其 HiFi verb 是否定义了 CaptureDevices：
grep -A20 'HiFi' /usr/share/alsa/ucm2/conf.d/rockchip_es8388/rockchip,es8388-codec.conf | head -40
echo "=== 或同目录其他文件 ==="
ls /usr/share/alsa/ucm2/conf.d/rockchip_es8388/
grep -rn 'Capture' /usr/share/alsa/ucm2/conf.d/rockchip_es8388/ | head -10
echo DONE
