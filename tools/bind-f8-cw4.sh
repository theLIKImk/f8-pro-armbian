#!/bin/sh
# 设备没创建。echo 到 new_device 的返回值检查 —— 上次 tee 吞掉了错误。直接测：
echo cw2015-battery 6-0062 > /sys/bus/i2c/devices/i2c-6/new_device 2>/tmp/f8-newdev.err
echo "rc=$?"
cat /tmp/f8-newdev.err
echo "---"
dmesg | tail -5
echo DONE
