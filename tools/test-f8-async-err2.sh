#!/bin/sh
sudo -n dmesg | grep -iE 'v4l2_async|async_register|registered subdev' | tail -10
echo M1
# sensor probe 后紧接着的日志（找失败点）：
sudo -n dmesg | grep -A5 'detected gc5035 sensor' | tail -10
echo M2
