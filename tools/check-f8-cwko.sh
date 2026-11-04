#!/bin/sh
# cw2015_battery.ko 已在 10-28 编译好（456KB，6.1.115）！
# 1. 验证模块 vermagic 匹配
echo "=== 模块信息 ==="
modinfo /var/tmp/f8-pro-armbian/extra-modules-6.1.115/cw2015_battery.ko | grep -E 'vermagic|filename|license' | head -3
echo DONE
