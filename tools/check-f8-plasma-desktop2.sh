#!/bin/sh
dpkg -L plasma-desktop 2>/dev/null | grep -i battery | head -5
dpkg -L plasma-desktop-data 2>/dev/null | grep -i 'plasmoids/org.kde.plasma.battery' | head -5
echo "---data 包 plasmoids 列表:"
dpkg -L plasma-desktop-data 2>/dev/null | grep 'plasmoids/org.kde' | grep metadata.json
echo DONE
