#!/bin/sh
# WP 仍无 source。看 wireplumber 日志找它为什么跳过 Mic：
journalctl --user -u wireplumber -b --no-pager -q 2>/dev/null | grep -iE 'mic|capture|source|profile' | tail -12
echo "=== 检查 UCM verb 是否启用（WP 依赖 UCM verb 内的设备） ==="
sudo -n alsaucm -b - <<'EOF'
open rockchip,es8388-codec
set _verb HiFi
get _devices
EOF
echo DONE
