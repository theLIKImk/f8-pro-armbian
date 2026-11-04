#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/1601
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus
dpkg -L feedbackd feedbackd-common
for f in /usr/lib/udev/rules.d/*feedback* /usr/lib/systemd/user/feedbackd.service /usr/share/dbus-1/services/org.sigxcpu.Feedback.service; do
  test ! -f "$f" || { echo "FILE: $f"; cat "$f"; }
done
systemctl --user status feedbackd.service --no-pager || true
gdbus introspect --session --dest org.sigxcpu.Feedback --object-path /org/sigxcpu/Feedback || true
journalctl --user -u feedbackd --no-pager -n 25
