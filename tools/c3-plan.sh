#!/bin/bash
# C3-v2 方案：官方 headers 虽然没带 sensor 源码文件，但 Makefile/Kconfig 引用它们，
# 且设备上已有编译好的 gc5035.ko（C2 已正常加载）。
# 最小代价方案：从自建树拷 gc5035.c/ov8858.c 两个源文件到官方 headers 树的
# drivers/media/i2c/，官方源码版本 6.1.115 与 6.1.172 的 sensor 驱动 API 差异小
# （Rockchip sensor 驱动版本号 gc5035 00.01.05/ov8858 00.01.06 与官方 Image 一致）。
# 但跨版本编译有 ABI 风险 —— 更稳的方法：直接改 Kconfig 为 y + 用设备上的
# headers 在设备上重编？headers 无源码编不了。
#
# 最稳做法：**用官方 headers + 自建树 sensor 源码，在 WSL 里 out-of-tree 编译
# gc5035.ko/ov8858.ko（官方 6.1.115 ABI）** —— 这正是项目 10-28 已经做过的事！
# /var/tmp/f8-pro-armbian/extra-modules-6.1.115/ 有 bq25890 和 cw2015 编译产物。
# sensor 驱动当初为什么没这么编？因为 C1/C2 时 sensor 模块已能加载（只是时序问题）。
#
# 但 early-load 问题依旧：模块再干净也要等用户态。所以还是要内编。
# **真正可行方案：把官方 vendor Image 的 gc5035 驱动改为内建需要官方源码重编 Image
# —— 没源码。替代：内核启动后 rkcif notifier 已完成 → 我们需要 rkcif 重新扫描。
# 关键发现回顾：C1 的 CIF 热重绑 Oops 是 rkcif_do_soft_reset 在 runtime_resume 里。
# 而 v4l2-async 框架：notifier complete 后，新注册 subdev 会调用 notifier 的
# complete 回调吗？不会。但 rkcif 的 sensor 信息更新走 rkcif_update_sensor_info
# （streamon 时调用）—— 它直接 walk media graph 找 sensor subdev！
# media graph walk 找的是 entity 链：video → cif → mipi-csi2 → dphy → sensor。
# sensor subdev 注册后 media graph 里就会有 sensor entity（dphy 的 async notifier
# 会为 sensor 创建 link）—— 但 dphy notifier 也 complete 了。
# 除非：**同时把 dphy 也 reset**？C1 Oops 就是这么来的。
#
# 最后一招（完全无风险）：**让 rkcif/dphy/mipi-csi2 也变成模块**！官方 Image 里它们
# 是内建 —— 但如果我们在 initramfs 里用 early userspace 之前加载？不可能。
#
# 终极可行方案：**接受时序，用官方 Image 的 late-binding 能力**：
# 重新测试 —— 也许 v4l2_async 的 fwnode 匹配允许迟到 subdev 加入已完成 notifier？
# 立即在 C2 设备上实验：rmmod gc5035; modprobe gc5035 —— 观察 media 图是否出现 sensor！
echo "下一步：在 C2 设备上实测 sensor 模块重载是否能重建 media 链（不碰 CIF unbind）"
