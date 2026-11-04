#!/bin/sh
ls /sys/module/rkcif* 2>/dev/null
echo M1
# 参数可能挂在别的名字（模块内建时 module 名是 rkcif? 或 param 在 build-in 模块目录）：
find /sys/module -maxdepth 1 -name '*cif*' 2>/dev/null
echo M2
# 查 dev.c 里 module_param_call 的注册名（内建模块 param 目录 = module name）：
echo "param name from source: clr_unready_dev (module=rkcif)"
echo MARKER_DONE
