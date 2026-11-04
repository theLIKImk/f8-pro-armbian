#!/bin/sh
# 关键发现：内核命令行含 `cpufreq.off=1` + `initcall_blacklist=rockchip_cpufreq_driver_init`
# —— 这是之前项目（U1 USB 试验时代）为了稳定故意关掉 cpufreq 的！
# 所以现在 CPU 固定频率、无 governor，power modes 无从谈起。
# 确认当前频率：
for cpu in 0 4; do
  echo "cpu$cpu:"
  cat /sys/devices/system/cpu/cpu$cpu/cpufreq/scaling_cur_freq 2>/dev/null || echo "  no cpufreq"
done
dmesg | grep -iE 'cpufreq-dt|scaling' | head -5
echo "---"
# 还有 f8_usb_u1=1 和 f8-desktop.target —— 这是 U1 时代的 boot！
# 而当前 rootfs 是 U5。BOOT 分区是 U5 的（含 USB 服务），但 cmdline 还是旧的。
echo DONE
