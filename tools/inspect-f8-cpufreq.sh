#!/bin/sh
# cpufreq 路径 glob 没展开。直接看 cpu0：
ls /sys/devices/system/cpu/cpu0/cpufreq/ 2>/dev/null || echo no-cpufreq-cpu0
echo "---"
ls /sys/devices/system/cpu/cpu0/ | head -15
echo "---"
# vendor 内核 RK3588S 用 cpufreq? 查 dtb 里 dvfs 和实际驱动：
ls /sys/bus/platform/drivers/ | grep -iE 'cpufreq|dvfs' 
echo "---"
dmesg | grep -iE 'cpufreq|dvfs' | head -8
echo DONE
