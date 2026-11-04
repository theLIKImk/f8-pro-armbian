#!/bin/sh
# tee 输出没显示错误码，看是否实际创建了设备：
ls /sys/bus/i2c/devices/ | grep 62
echo "---"
ls -la /sys/bus/i2c/devices/i2c-6/ | grep -E '0062' 
echo "---"
# 如果设备在但没绑定驱动（因为没有 DT compatible）—— 检查 driver 链接：
readlink /sys/bus/i2c/devices/6-0062/driver 2>/dev/null || echo no-driver-bound
cat /sys/bus/i2c/devices/6-0062/name 2>/dev/null
echo DONE
