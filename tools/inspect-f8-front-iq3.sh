#!/bin/sh
f=/opt/f8-pro-camera/aiq-v6-c4/iqfiles/gc5035_XHG-RKX11F-V5_HR232H65.json
sudo -n sh -c "grep -n 'AecFrameRateMode' $f | head -2"
sudo -n sh -c "grep -n 'isFpsFix\|FpsValue' $f | head -4"
echo M1
sudo -n sh -c "grep -n 'AecFrameRateMode\|isFpsFix\|FpsValue' /opt/f8-pro-camera/aiq-v6-c4/iqfiles-fps14/ov8858_HS5885-BNSM1018-V01_default.json | head -4"
echo M2
