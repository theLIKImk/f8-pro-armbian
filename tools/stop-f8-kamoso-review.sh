#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/1601
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus
if systemctl --user is-active --quiet f8-kamoso-review01.service; then
    systemctl --user stop f8-kamoso-review01.service
fi
cat /proc/sys/kernel/random/boot_id
pgrep -af 'kamoso|aiq-backend|v4l2-ctl' || true
