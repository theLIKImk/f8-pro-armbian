#!/bin/sh
# battery widget 在 plasma-desktop？plasma-desktop 未装（依赖链列出它是 dep of
# plasma-workspace 6.6.6 升级候选）。直接确认：
dpkg -l plasma-desktop 2>/dev/null | tail -1 || echo NOT_INSTALLED
echo "---"
apt-cache policy plasma-desktop | head -5
echo DONE
