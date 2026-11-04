#!/bin/sh
# 手工 cset 成功 => UCM 失败可能因为以 sudo(root) 跑时 mixer 设备权限/上下文不同？
# 或者 UCM 语法里单引号嵌套问题：cset "name='Main Mic' on" —— 试简化为去空格枚举：
# 先绕开：把 EnableSequence 里逐项简化为确定可用形式（去掉 Main/Headset Mic 行，
# 它们已经 on）。同时最终目标是 WP 建 source；其实 UCM Sequence 失败不是重点，
# 重点可能是 WP 需要 UCM verb 支持 CapturePCM。先看 WP 有没有忽略 Mic 设备：
sudo -n sed -i "s/        cset \"name='Main Mic' on\"//" /usr/share/alsa/ucm2/F8-PRO/HiFi.conf
sudo -n sed -i "s/        cset \"name='Headset Mic' off\"//" /usr/share/alsa/ucm2/F8-PRO/HiFi.conf
sudo -n alsaucm -b - <<'EOF'
open rockchip,es8388-codec
set _verb HiFi
set _enadev Mic
EOF
echo "rc=$?"
sleep 2
pactl list sources short
echo DONE
