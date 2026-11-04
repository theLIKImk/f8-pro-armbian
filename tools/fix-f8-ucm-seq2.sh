#!/bin/sh
# 删除残留的 Main Mic 行（sed 模式没匹配到）：
sudo -n sed -i "/Main Mic/d" /usr/share/alsa/ucm2/F8-PRO/HiFi.conf
sudo -n grep -c "Main Mic" /usr/share/alsa/ucm2/F8-PRO/HiFi.conf
sudo -n alsaucm -b - <<'EOF'
open rockchip,es8388-codec
set _verb HiFi
set _enadev Mic
EOF
echo "rc=$?"
sleep 2
pactl list sources short
echo DONE
