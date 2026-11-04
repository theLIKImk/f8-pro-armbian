#!/bin/sh
echo "=== GC5035 IQ 关键字段（对照 OV8858 已修复版）==="
f=/opt/f8-pro-camera/aiq-v6-c4/iqfiles/gc5035_XHG-RKX11F-V5_HR232H65.json
echo "--- version/isp 声明:"
sudo -n head -30 "$f" | grep -iE 'version|isp|target' | head -5
echo "--- sub_scene 内容:"
sudo -n grep -A6 '"sub_scene"' "$f" | head -10
echo "--- AE 帧率策略（后摄修复点）:"
sudo -n grep -B2 -A4 'AecFrameRateMode' "$f" | head -12
echo "--- 对照 OV8858 修复后的 AE 帧率:"
sudo -n grep -B2 -A4 'AecFrameRateMode' /opt/f8-pro-camera/aiq-v6-c4/iqfiles-fps14/ov8858_HS5885-BNSM1018-V01_default.json | head -12
echo MARKER_DONE
