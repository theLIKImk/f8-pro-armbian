#!/bin/sh
# 全部已装包都不含 org.kde.plasma.battery。用 Contents 文件精确找：
# 先看 sources 和架构，然后下载 Contents-arm64.gz 查询（不装 apt-file）：
grep -rE '^deb ' /etc/apt/sources.list /etc/apt/sources.list.d/ 2>/dev/null | head -3
echo DONE
