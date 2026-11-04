#!/bin/sh
# 持久化方案：
# 1) 模块开机加载：/etc/modules-load.d/
# 2) 设备绑定：驱动需要 DT 节点或 new_device。BOOT DT 修改需要刷 boot ——
#    但更轻的方案：用 systemd oneshot 服务在开机后做 new_device 绑定
#    （与现有 f8-usb-otg.service 模式一致，不动 BOOT）。
# 3) supply 报错 -19 是因为驱动找 vdd-supply regulator；DT 节点将来可补，
#    但不影响容量/状态读数。
set -e
echo "=== 1. modules-load ==="
echo "cw2015_battery" | sudo -n tee /etc/modules-load.d/f8-cw2015.conf
echo "=== 2. 绑定服务 ==="
sudo -n tee /usr/lib/systemd/system/f8-battery-cw2015.service > /dev/null <<'EOF'
[Unit]
Description=F8 CW2015 battery i2c bind (until DT node lands in BOOT)
After=multi-user.target
Wants=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo cw2015 0x62 > /sys/bus/i2c/devices/i2c-6/new_device'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
sudo -n systemctl daemon-reload
sudo -n systemctl enable f8-battery-cw2015.service
echo DONE
