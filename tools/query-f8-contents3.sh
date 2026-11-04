#!/bin/sh
# 没有 lz4 模块。用 zstd/lz4 CLI 或 apt 文件在线查询。先试系统 lz4 命令：
which lz4 zstd 2>/dev/null
echo "---尝试 CLI:"
lz4 -dc /var/lib/apt/lists/ports.ubuntu.com_dists_resolute_Contents-arm64.lz4 2>/dev/null | grep 'plasmoids/org.kde.plasma.battery/metadata.json' | head -3
echo "---updates gzip:"
zcat /var/lib/apt/lists/ports.ubuntu.com_dists_resolute-updates_Contents-arm64.gz 2>/dev/null | grep 'plasmoids/org.kde.plasma.battery/metadata.json' | head -3
echo DONE
