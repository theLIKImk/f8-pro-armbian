#!/bin/sh
for cpu in 0 4; do
  echo "cpu$cpu: $(cat /sys/devices/system/cpu/cpu$cpu/cpufreq/scaling_cur_freq 2>/dev/null || echo no-cpufreq)"
done
dmesg | grep -iE 'cpufreq' | head -6
echo "---current cmdline f8 flags:"
cat /proc/cmdline | tr ' ' '\n' | grep -E 'f8_|cpufreq|systemd.unit' 
echo DONE
