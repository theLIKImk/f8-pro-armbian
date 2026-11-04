#!/bin/sh
# CW2015 在 0x62 响应（未绑定）！BQ25890 在 0x6a 显示 UU（被 f8-otg-vbus 占用）。
# 检查内核是否启用 CW2015 驱动：
echo "=== CW2015 驱动模块 ==="
grep -i cw2015 /lib/modules/$(uname -r)/modules.builtin 2>/dev/null && echo builtin
modinfo cw2015_battery 2>/dev/null | head -3 || modinfo cw2015 2>/dev/null | head -3 || echo "no module info"
find /lib/modules/$(uname -r) -name '*cw20*' -o -name '*cw2015*' 2>/dev/null
echo "=== vendor 6.1.115 的 CONFIG_BATTERY_CW2015 ==="
grep -i CW2015 /boot/config-$(uname -r) 2>/dev/null || echo "no /boot/config"
echo DONE
