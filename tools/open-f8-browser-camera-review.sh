#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess,time
from pathlib import Path
runtime=Path('/run/user/1601');sockets=[p.name for p in runtime.glob('wayland-*') if p.is_socket()];assert sockets
env={**os.environ,'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus'}
p=subprocess.run(['systemd-run','--user','--collect','--unit=f8-chromium-camera-review01','--setenv=WAYLAND_DISPLAY='+sockets[0],'/usr/local/bin/f8-chromium-camera'],env=env,capture_output=True,text=True,timeout=10);assert p.returncode==0,p.stderr
time.sleep(4)
print(json.dumps({'launch_requested':True,'test_page':'file:///usr/local/share/f8-pro/camera-browser-test.html','camera_permission':'normal user prompt, not auto-granted','status':subprocess.run(['systemctl','--user','show','f8-chromium-camera-review01','-p','ActiveState','-p','SubState'],env=env,capture_output=True,text=True).stdout},indent=2))
PY
