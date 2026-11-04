#!/bin/sh
# 部署模块到平板并加载（不动充电参数——CW2015 是只读电量计，BQ25890 充电仍禁用）
set -e
echo "=== 1. 传输模块 ==="
scp -i /var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519 \
    -o BatchMode=yes -o IdentitiesOnly=yes \
    -o UserKnownHostsFile=/var/tmp/f8-pro-archlinux-20261027/test-known-hosts \
    /var/tmp/f8-pro-armbian/extra-modules-6.1.115/cw2015_battery.ko \
    f8test@192.168.1.227:/tmp/cw2015_battery.ko
echo "=== 2. 设备上安装到 modules 目录 ==="
ssh -T -i /var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519 \
    -o BatchMode=yes -o IdentitiesOnly=yes \
    -o UserKnownHostsFile=/var/tmp/f8-pro-archlinux-20261027/test-known-hosts \
    f8test@192.168.1.227 \
    'sudo -n install -m 0644 /tmp/cw2015_battery.ko /lib/modules/6.1.115-vendor-rk35xx/updates/cw2015_battery.ko && sudo -n depmod -a && echo INSTALLED'
echo DONE
