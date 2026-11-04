#!/bin/sh
# DT 完整带 OPP 表（cluster0/1/2）和 cpu-supply —— 万事俱备，只差 cpufreq 被 cmdline 挡了。
# cpufreq.off=1 是 cpufreq_core 的参数。initcall_blacklist 挡的是 vendor rockchip 驱动。
# cpufreq-dt 驱动：检查它是否也被挡（cpufreq.off=1 会挡所有 cpufreq init）。
#
# 但重要问题：**为什么当时关 cpufreq？** HANDOFF 提到"暂停 vendor cpufreq init"
# 是因为 I2C0 m2 冲突修正 RK8602/3 时（第二十八轮之前），后来 G6/r5/r6 系列继续保留。
# 现在系统已稳定运行 USB/音频/电池，恢复 cpufreq 是合理下一步，但必须：
# 1. 确认 cpu-supply regulator 正常（rk8602/3 已确认工作）
# 2. 检查 DT cooling/thermal 就绪
# 测试路径：先在运行态尝试重新让 cpufreq-dt probe —— 内核参数无法运行时撤销，
# 但 platform driver 可以手动 probe（如果 cpufreq.off 只影响注册时序）：
echo "=== 尝试手动 probe cpufreq-dt ==="
echo cpu0 | sudo -n tee /sys/bus/platform/drivers/cpufreq-dt/bind 2>&1 | head -2
echo "rc=$?"
ls /sys/devices/system/cpu/cpu0/cpufreq/ 2>/dev/null | head -5
echo "---"
dmesg | tail -3
echo DONE
