#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess,time
from pathlib import Path
assert os.getuid()==1601
assert os.access('/dev/input/f8-cover',os.R_OK) and os.access('/dev/input/f8-haptic',os.W_OK)
runtime=Path('/run/user/1601');env={**os.environ,'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus'}
subprocess.run(['systemctl','--user','daemon-reload'],env=env,check=True,timeout=8);subprocess.run(['systemctl','--user','start','f8-cover-screen.service'],env=env,check=True,timeout=8)
sockets=[p.name for p in runtime.glob('wayland-*') if p.is_socket()];assert sockets
p=subprocess.run(['systemd-run','--user','--collect','--unit=f8-cover-test-review01','--setenv=QT_QPA_PLATFORM=wayland','--setenv=WAYLAND_DISPLAY='+sockets[0],'/usr/local/bin/f8-cover-test'],env=env,capture_output=True,text=True,timeout=8);assert p.returncode==0,p.stderr
time.sleep(2)
print(json.dumps({'observer':json.loads((Path.home()/'.cache/f8-cover/status.json').read_text()),'gui_requested':True,'motor_active':Path('/sys/devices/platform/f8-cover-haptic/motor_active').read_text().strip()},indent=2))
PY
