#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/1601
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus
# The daemon exports its haptic interface only when a motor exists at startup.
pkill -u "$(id -u)" -x feedbackd || true
sleep 1
gdbus introspect --session --dest org.sigxcpu.Feedback --object-path /org/sigxcpu/Feedback
test -f ~/.config/plasmakeyboardrc.before-f8-haptic || cp ~/.config/plasmakeyboardrc ~/.config/plasmakeyboardrc.before-f8-haptic
kwriteconfig6 --notify --file plasmakeyboardrc --group General --key vibrationEnabled true
kwriteconfig6 --notify --file plasmakeyboardrc --group General --key vibrationMs 30
cat ~/.config/plasmakeyboardrc
