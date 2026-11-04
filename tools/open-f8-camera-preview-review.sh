#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess
from pathlib import Path
assert os.getuid()==1601
env={**os.environ,'XDG_RUNTIME_DIR':'/run/user/1601','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus'}
sockets=[p.name for p in Path('/run/user/1601').glob('wayland-*') if p.is_socket()];assert sockets
p=subprocess.run(['systemd-run','--user','--collect','--unit=f8-camera-preview-review01',
 '--setenv=QT_QPA_PLATFORM=wayland','--setenv=WAYLAND_DISPLAY='+sockets[0],'/usr/local/bin/f8-camera-preview'],
 env=env,capture_output=True,text=True,timeout=10)
assert p.returncode==0,p.stderr
print(json.dumps({'launch_requested':True,'unit':'f8-camera-preview-review01','autostart_capture':False,'stderr':p.stderr},indent=2))
PY
