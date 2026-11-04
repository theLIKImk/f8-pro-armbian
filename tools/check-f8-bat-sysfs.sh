#!/bin/sh
# probe 成功了（power_supply 目录存在）！只是 supply 链缺（没电压读取）。
echo "=== BAT 设备属性 ==="
for f in /sys/class/power_supply/cw2015-battery/*; do
  echo "$(basename $f): $(cat $f 2>/dev/null | head -1)"
done 2>/dev/null | head -15
echo "---"
ls /sys/class/power_supply/
echo "---"
# upower 现在能看到吗
export XDG_RUNTIME_DIR=/run/user/1601
upower -e 2>/dev/null
echo DONE
