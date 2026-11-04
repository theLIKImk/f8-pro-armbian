#!/bin/sh
sudo -n sh -c 'cat > /usr/lib/systemd/system/f8-battery-cw2015.service' <<'EOF'
[Unit]
Description=F8 CW2015 battery i2c bind (until DT node lands in BOOT)
After=systemd-modules-load.service
Wants=systemd-modules-load.service

[Service]
Type=oneshot
ExecStart=/bin/sh -c "for i in 1 2 3; do echo cw2015 0x62 > /sys/bus/i2c/devices/i2c-6/new_device && break || sleep 2; done"
RemainAfterExit=yes

[Install]
WantedBy=sysinit.target
EOF
sudo -n systemctl daemon-reload
sudo -n systemctl reenable f8-battery-cw2015.service 2>/dev/null || sudo -n systemctl enable f8-battery-cw2015.service
echo DONE
