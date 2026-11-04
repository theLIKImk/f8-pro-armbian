#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/1601
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus
systemd-run --user --collect --unit=f8-first-run-review-r1 --setenv=QT_QPA_PLATFORM=wayland --setenv=WAYLAND_DISPLAY=wayland-0 /usr/bin/python3 "$HOME/.cache/f8-first-run-preview-r1/first-run.py" --preview
