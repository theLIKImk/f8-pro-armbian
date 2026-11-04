#!/bin/sh
# lz4 装好了但 grep 无输出 —— resolute 主 Contents 里没有该路径？
# 完整确认 + 大小写宽匹配:
lz4 -dc /var/lib/apt/lists/ports.ubuntu.com_dists_resolute_Contents-arm64.lz4 2>/dev/null > /tmp/f8-contents.txt
wc -l /tmp/f8-contents.txt
grep -i 'org.kde.plasma.battery' /tmp/f8-contents.txt | head -5
echo "---batterymonitor:"
grep -i 'batterymonitor' /tmp/f8-contents.txt | head -3
echo DONE
