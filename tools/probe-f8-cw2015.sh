#!/bin/sh
# 内核没编 CW2015 驱动，也没模块。这是问题核心。
# 检查 DT 里有没有 cw2015 节点（若 vendor DT 有但驱动没编，节点变 orphan）：
echo "=== 运行 DT 中搜 cw/bat 节点 ==="
sudo -n find /proc/device-tree -iname '*cw2015*' -o -iname '*cw20*' 2>/dev/null | head -5
echo "---"
# 手动读 CW2015 ID 寄存器验证芯片存在（0x00 chip_id 应返回 0x40-0x4x 区域）：
sudo -n i2cget -y 6 0x62 0x00 2>&1
sudo -n i2cget -y 6 0x62 0x03 2>&1
echo DONE
