#!/bin/sh
# alsaucm open 报 -2：UCM 找不到。但 WP 显然在用 UCM（profile HiFi 是 UCM 提供的）。
# UCM 名匹配规则：/usr/share/alsa/ucm2/conf.d/<name>/<name>.conf
# 我们的 conf 在 conf.d/rockchip_es8388/rockchip,es8388-codec.conf —— UCM 名是
# "rockchip,es8388-codec"？或由 UCM_MANAGER_NAME。看当前 UCM 绑定：
sudo -n ls -la /var/lib/alsa/ 2>/dev/null
sudo -n cat /proc/asound/card0/ucm 2>/dev/null
echo "--- 试 UCM 名 = conf 文件名去后缀:"
sudo -n alsaucm open 'rockchip,es8388-codec' 2>&1 | head -1
sudo -n alsaucm set _verb HiFi 2>&1 | head -1
sudo -n alsaucm set _enadev Mic 2>&1 | head -1
sleep 2
pactl list sources short
echo DONE
