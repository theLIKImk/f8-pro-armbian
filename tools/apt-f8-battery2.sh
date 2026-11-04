#!/bin/sh
# Plasma 6.6 里 battery applet 就在 plasma-workspace 主包，但 Ubuntu 只装了 14 个
# plasmoids 而主包应该有几十个 —— 很可能 Ubuntu 用 variants 拆分且 battery widget
# 在 plasma-desktop 或独立。全库搜文件路径：
apt-cache search 'plasma.*battery' 2>/dev/null
echo "---用 Contents 索引查（如果 apt-file 不可用就直接装含它的包）"
# Ubuntu 拆分包习惯：plasma-workspace 精简后 battery 在 plasma-desktop-data?
apt-cache show plasma-desktop 2>/dev/null | grep -iE 'battery|Widget' | head -3
echo "---"
# 最直接：apt-get install --dry-run 看 org.kde.plasma.battery 由谁提供：
apt-get install --dry-run plasma-workspace 2>&1 | grep -iE 'battery|升级|新安装' | head -5
echo "---"
apt list --installed 2>/dev/null | grep -cE 'plasma'
echo DONE
