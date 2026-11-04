#!/bin/sh
# card 只有 HiFi profile 且只含输出 port，没有输入 profile/port。
# 这是 WirePlumber 的 profile 集（UCM 或 alsa-card-profiles）决定的。
# 内核侧 capture PCM 是存在的（arecord 可用）。看 UCM 是否存在：
ls /usr/share/alsa/ucm2/conf.d/*es83* /usr/share/alsa/ucm2/Rockchip 2>/dev/null
echo "--- card UCM 目录:"
find /usr/share/alsa/ucm2 -iname '*rockchip*' -o -iname '*rk3588*' -o -iname '*es83*' 2>/dev/null
echo "--- alsa UCM verb for card:"
sudo -n alsaucm -c 0 list _verbs 2>&1 | head -10
echo "--- 内核侧 ASoc PCM 是否有 capture device 已注册给 WP：
cat /proc/asound/card0/pcm0c/info | head -3"
echo DONE
