#!/bin/sh
echo "=== rkisp0-vir0 完整报错上下文 ==="
sudo -n dmesg | grep -B3 -A3 'check rkisp_mainpath link or isp input' | tail -20
echo "=== media2 拓扑中 ISP input 链接状态 ==="
sudo -n media-ctl -d /dev/media2 -p 2>/dev/null | grep -B2 -A4 'ENABLED\|DISABLED' | head -30
echo DONE
