#!/bin/sh
echo "OV fps14 AecFrameRateMode:"
sudo -n grep -A3 '"AecFrameRateMode"' /opt/f8-pro-camera/aiq-v6-c4/iqfiles-fps14/ov8858_HS5885-BNSM1018-V01_default.json | head -5
echo "M1"
echo "GC5035 AecFrameRateMode:"
sudo -n grep -A3 '"AecFrameRateMode"' /opt/f8-pro-camera/aiq-v6-c4/iqfiles/gc5035_XHG-RKX11F-V5_HR232H65.json | head -5
echo "M2"
echo "GC5035 OTP 相关（AWB/LSC flag 完整性需运行时查）:"
sudo -n grep -c 'awb' /opt/f8-pro-camera/aiq-v6-c4/iqfiles/gc5035_XHG-RKX11F-V5_HR232H65.json
echo "MARKER_DONE"
