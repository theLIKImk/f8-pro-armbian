#!/bin/sh
# rkisp SDITF 路径：sditf 通过 rkisp_rawrd*_m (mainpath raw read) 喂 ISP pad0。
# RAW 链接未 ENABLED —— 需用 media-ctl -l 显式接通 rawrd0_m -> isp:0。
# GC5035/OV8858 都是 RAW sensor，走 mainpath raw read (rawrd0_m)。
# 分别为 media2/3 接通（可逆，属标准 media-ctl 配置，不触热重绑禁令）：
echo "=== enable media2 rawrd0 -> isp ==="
sudo -n media-ctl -d /dev/media2 -l '"rkisp_rawrd0_m":0->"rkisp-isp-subdev":0[1]' 2>&1
echo "=== enable media3 rawrd0 -> isp ==="
sudo -n media-ctl -d /dev/media3 -l '"rkisp_rawrd0_m":0->"rkisp-isp-subdev":0[1]' 2>&1
echo "=== verify ==="
sudo -n media-ctl -d /dev/media2 -p 2>/dev/null | grep -A2 'rawrd0_m' | head -4
echo DONE
