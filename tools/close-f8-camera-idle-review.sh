#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/1601
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus
python3 -I - <<'PY'
import subprocess
p=subprocess.run(['fuser','/dev/video22','/dev/video31'],capture_output=True,text=True)
assert not p.stdout.strip(),'Camera is in use; preserve current recording'
PY
if systemctl --user is-active --quiet f8-camera-preview-review01.service; then
 systemctl --user stop f8-camera-preview-review01.service
fi
