#!/bin/sh
# modprobe rc=0 但 lsmod 无 —— 模块内置？不，可能模块名不带 _battery。再查：
sudo -n modprobe -r cw2015_battery 2>/dev/null
sudo -n insmod /lib/modules/6.1.115-vendor-rk35xx/updates/cw2015_battery.ko 2>&1
echo "insmod rc=$?"
lsmod | grep -i cw
echo "---"
cat /proc/modules | grep -i cw
echo DONE
