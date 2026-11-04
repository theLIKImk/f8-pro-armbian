#!/bin/bash
# 核心结论：
# C1/C2 用的 kernel 是 **Armbian 官方 vendor-rk35xx Image**（build@armbian 2026-07-15），
# 不是自建树编译的。自建树（kernel-config-build）是 6.1.172 主线 RK 分支源码，编译出的是
# 不同内核 —— C3 我错误地用了它，还带着 cpufreq 实验时代被 blacklisted 的 cmdline。
# 正确修复：需要 Armbian 官方 vendor 内核源码 + 官方 config，把 gc5035/ov8858 改 =y 重编。
# 检查 WSL 里有没有 vendor 内核源码：
ls /var/tmp/f8-pro-armbian/linux-rockchip-config/.git 2>/dev/null && git -C /var/tmp/f8-pro-armbian/linux-rockchip-config log --oneline -1
git -C /var/tmp/f8-pro-armbian/linux-rockchip-config branch -a 2>/dev/null | head -5
git -C /var/tmp/f8-pro-armbian/linux-rockchip-config remote -v 2>/dev/null | head -2
