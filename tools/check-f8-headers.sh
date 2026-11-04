#!/bin/sh
# DT 里 i2c6 只有 es8388，fusb302/otg/0x62 都是运行时绑定的（insmod 或固定节点在别处）。
# 0x62 有响应、寄存器值 0x73/0x6d —— CW2015 上电默认 VCELL，芯片活着。
# 方案：不重编内核 —— 用 DKMS/树外模块编译 cw2015 驱动（官方 kernel 有 cw_bat 驱动源码，
# vendor 6.1 源码里也有）。或者更轻：用 userspace 读 CW2015 + upower 不支持自定义；
# 标准做法：DT 新增 cw2015 节点 + 编译树外模块。
# 先检查内核 headers 是否在设备上（之前项目在 WSL 编过 6.1.115 headers）：
ls /usr/src/ 2>/dev/null | head -5
uname -r
echo "---"
ls /lib/modules/$(uname -r)/build 2>/dev/null && echo build-symlink-ok || echo no-build-dir
echo DONE
