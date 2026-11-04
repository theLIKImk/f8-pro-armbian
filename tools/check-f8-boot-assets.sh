#!/bin/sh
# cpufreq-dt bind 失败（No such device）—— cpufreq.off=1 在 core 层面把
# cpufreq 子系统停了（cpufreq_driver_register 直接返回），运行时无法解除。
#
# 结论：要启用三档电源模式，必须重刷 BOOT（去掉 cpufreq.off=1 与
# initcall_blacklist）。这是项目早期（I2C0 冲突、供电适配时代）的保守参数，
# 现在供电链已验证（RK8602/3 在 R2 轮就绑定成功、R5/R6 稳定）。
#
# 但注意 HANDOFF 明确警告：修改 BOOT = 只刷 boot0x8000，流程已多次验证。
# 且过去 U1 试验失败教训：改动要单一、可回退。
#
# 方案（最小改动）：重建 BOOT-only 镜像 —— 用当前在用的 U5/A3 基线 BOOT，
# 仅改 cmdline（去 cpufreq.off=1 和 initcall_blacklist=rockchip_cpufreq_driver_init，
# 保留其它一切），让 rockchip vendor cpufreq 正常注册（它支持 SCHEDUTIL 等 governor
# 并含三集群 OPP）。
#
# 先检查本地是否有 U5 BOOT 源与打包工具链：
ls /var/tmp/f8-pro-armbian/ 2>/dev/null | grep -iE 'boot|u5|u4' | head -10
ls /var/tmp/f8-pro-armbian/official-f8-native-usb-u5* 2>/dev/null | head -5
echo DONE
