#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/1601
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus
python3 -I - <<'PY'
import os,subprocess
p=subprocess.run(['pgrep','-u',str(os.getuid()),'-af','gst-launch-1.0.*avimux'],capture_output=True,text=True)
assert not p.stdout.strip(),'Preserve active recording'
PY
if systemctl --user is-active --quiet f8-camera-preview-review01.service; then
 systemctl --user stop f8-camera-preview-review01.service
fi
