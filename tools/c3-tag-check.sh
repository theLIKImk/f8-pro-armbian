#!/bin/bash
# 版本核对结论：
# 自建树 = 6.1.172（commit 85233a85b），官方 vendor Image = 6.1.115。不同版本！
# HANDOFF 早有记录：“26.8.1 Image 哈希 a67daf71…0c37b7 不同于旧 26.8.3 同名 6.1.115，旧 headers/extra ko 不能假定兼容”
# 正确路径：找 6.1.115 对应的源码（rk-6.1-rkr5 或更早 tag），用官方 config 重编。
# 先查这个 git 树有没有 6.1.115 相关 tag/branch：
git -C /var/tmp/f8-pro-armbian/linux-rockchip-config tag | grep -iE '6\.1\.11|rk5' | head -5
git -C /var/tmp/f8-pro-armbian/linux-rockchip-config branch -a | head -10
