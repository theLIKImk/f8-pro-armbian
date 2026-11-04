#!/bin/sh
# resolute 主索引是 lz4 但系统没有 lz4 工具；updates/security 是 gz 已查无。
# Armbian resolute-desktop 仓库可能有。查 armbian Contents:
ls /var/lib/apt/lists/ | grep -iE 'armbian.*Contents' | head -5
echo "---"
# Ubuntu 的 lz4：用 python 的 lz4 不可用，装 lz4 CLI（小工具）：
sudo -n apt-get install -y lz4 2>&1 | tail -1
lz4 -dc /var/lib/apt/lists/ports.ubuntu.com_dists_resolute_Contents-arm64.lz4 2>/dev/null | grep 'plasmoids/org.kde.plasma.battery/metadata.json' | head -3
echo DONE
