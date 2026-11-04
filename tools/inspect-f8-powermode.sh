#!/bin/sh
echo "=== 当前 CPU 调速器与频率 ==="
for c in /sys/devices/system/cpu/cpu[0-7]/cpufreq; do
  echo "$c: $(cat $c/scaling_governor 2>/dev/null) cur=$(cat $c/scaling_cur_freq 2>/dev/null) min=$(cat $c/scaling_min_freq 2>/dev/null) max=$(cat $c/scaling_max_freq 2>/dev/null)"
done 2>/dev/null | head -8
echo "=== 可用 governor ==="
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors 2>/dev/null
echo "=== CPU 集群结构 ==="
ls /sys/devices/system/cpu/ | grep -E 'cpu[0-9]' | head -10
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_frequencies 2>/dev/null | head -2
cat /sys/devices/system/cpu/cpu4/cpufreq/scaling_available_frequencies 2>/dev/null | head -2
echo "=== powerdevil profiles ==="
ls /usr/share/powerdevil/profiles/ 2>/dev/null || echo no-profiles-dir
echo "=== powerdevil 运行状态 ==="
ps aux | grep -v grep | grep powerdevil | head -2
echo "=== platform profile（若支持） ==="
cat /sys/firmware/acpi/platform_profile 2>/dev/null || echo no-acpi
ls /sys/class/powercap/ 2>/dev/null
echo DONE
