#!/bin/sh
# 先取证：pstore 里可能有 PM1 panic 记录！上次 PM1 panic=0 卡死时 console 输出
# 可能落进 ramoops。读 pstore：
sudo -n ls /sys/fs/pstore/ 2>/dev/null
sudo -n cat /sys/fs/pstore/console-ramoops-0 2>/dev/null | tail -40
echo DONE
