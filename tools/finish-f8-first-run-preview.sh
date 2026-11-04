#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/1601
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus
gdbus introspect --session --dest org.kde.Shutdown --object-path /Shutdown
systemctl --user stop f8-first-run-review-r1.service || true
printf 'motor_active='; cat /sys/devices/platform/f8-cover-haptic/motor_active
