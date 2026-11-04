#!/bin/sh
# powerdevil 在跑但 org.kde.plasma.battery 小组件缺失（plasma-workspace 拆分包）。
# Ubuntu 拆分：电池 widget 可能在 plasma-workspace-data 或独立包。搜索：
apt-cache search battery 2>/dev/null | grep -i plasma | head -5
echo "---"
apt-file list 2>/dev/null | grep org.kde.plasma.battery | head -3 || \
  apt-cache show plasma-workspace 2>/dev/null | grep -i battery | head -5
echo "---"
# 也查 powerdevil 是否完整（电池通知/亮度依赖）：
dpkg -L powerdevil 2>/dev/null | grep -E 'bin/|libexec' | head -5
echo "---"
# 系统托盘设置里 battery 图标的状态：
ls /usr/share/plasma/plasmoids/ | head -30
echo DONE
