#!/bin/sh
# config.lua.d 目录不存在（新版 WP 用 conf.d + .conf）。查 WP 1.6 的配置目录结构：
ls /usr/share/wireplumber/ 2>/dev/null | head
ls /usr/share/wireplumber/wireplumber.conf.d/ 2>/dev/null | head
echo "--- 主 conf:"
ls /usr/share/wireplumber/*.conf 2>/dev/null
echo DONE
