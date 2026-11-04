#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/1601
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus
export WAYLAND_DISPLAY=wayland-0
export XDG_SESSION_TYPE=wayland
unset QT_QPA_PLATFORM
python3 -I - <<'PY'
import json
from PyQt6.QtWidgets import QApplication
app=QApplication([])
print(json.dumps({'automatic_qt_platform':app.platformName(),'wayland_without_platform_override':app.platformName()=='wayland'}))
assert app.platformName()=='wayland'
PY
