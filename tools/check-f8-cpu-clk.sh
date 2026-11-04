#!/bin/sh
lscpu 2>/dev/null | grep -iE 'MHz|model name|model:' | head -4
echo "---"
cat /proc/cpuinfo | grep -m2 -E 'MHz|model name' 2>/dev/null
echo "---"
# 当前实际频率从 clk 读：
sudo -n cat /sys/kernel/debug/clk/clk_summary 2>/dev/null | grep -E 'cpu|cluster' | head -6
echo DONE
