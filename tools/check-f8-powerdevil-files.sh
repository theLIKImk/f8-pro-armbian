#!/bin/sh
# 关键发现：Plasma 6.6 中 battery applet 的 QML 已并入 powerdevil 包！
# powerdevil 已安装。检查它提供了哪些 applet 文件：
dpkg -L powerdevil 2>/dev/null | grep -iE 'plasma/applets|plasmoids' | head -10
echo "---"
dpkg -L powerdevil-data 2>/dev/null | grep -iE 'applets|plasmoids' | head -10
echo DONE
