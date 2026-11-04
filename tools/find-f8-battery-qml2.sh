#!/bin/sh
# batterymonitor QML 插件已在（qml 私有模块）。Contents 里没有 plasmoid QML
# 目录条目 —— 说明 Plasma 6.6 battery applet 的 UI 完全在 C++ 插件 + qml 私有模块，
# 无需 /usr/share/plasma/plasmoids/org.kde.plasma.battery 目录？
# 不对：applet 需要 metadata.json。再查 Contents 中 'plasma/battery'（不带 org.kde）：
lz4 -dc /var/lib/apt/lists/ports.ubuntu.com_dists_resolute_Contents-arm64.lz4 2>/dev/null | grep -E 'share/plasma/plasmoids.*battery' | head -5
echo "---补查 updates 索引:"
zcat /var/lib/apt/lists/ports.ubuntu.com_dists_resolute-updates_Contents-arm64.gz 2>/dev/null | grep -E 'share/plasma/plasmoids.*battery' | head -5
echo DONE
