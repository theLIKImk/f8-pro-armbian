#!/bin/sh
# CPU 全部固定在 816MHz（最低档）—— cpufreq 被关，SCMI 时钟停在保守频率。
# RK3588S: 4xA55(LITTLE) + 4xA76(big)。
# 要做省电/平衡/性能三档，需要先恢复 cpufreq。
# 问题：cmdline 是 BOOT 分区固化的（U5 时代为 USB 稳定关了 cpufreq）。
# 选项A：重做 BOOT 去掉 cpufreq.off —— 要刷机，风险较大；
# 选项B：检查 cpufreq.off=1 的语义 —— 它是内核参数，能运行时解除吗？不能。
#   但 initcall_blacklist 只挡 rockchip_cpufreq_driver_init（vendor 特定），
#   而 cpufreq-dt 驱动已注册（sysfs 有 driver）—— DT 里 cpu 节点若带
#   operating-points，或许能手动触发 cpufreq-dt probe？看 DT:
echo "=== DT cpu 节点 op-table ==="
sudo -n ls /proc/device-tree/cpus/ 2>/dev/null | head
sudo -n cat /proc/device-tree/cpus/cpu@0/operating-points-v2 2>/dev/null | head -2 || \
  sudo -n ls /proc/device-tree/cpus/cpu@0/ 2>/dev/null | head
echo "=== cpu0 节点有没有 opp 表引用 ==="
sudo -n ls /proc/device-tree/cpus/cpu@0/ 2>/dev/null
echo "=== opp-table-0 ==="
sudo -n ls /proc/device-tree/ 2>/dev/null | grep -i opp
echo DONE
