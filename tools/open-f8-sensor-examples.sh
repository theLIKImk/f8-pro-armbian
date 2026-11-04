#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess,time
from pathlib import Path
assert os.getuid()==1601
runtime=Path('/run/user/1601');env={**os.environ,'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus'}
sockets=[p.name for p in runtime.glob('wayland-*') if p.is_socket()];assert sockets
p=subprocess.run(['systemd-run','--user','--collect','--unit=f8-sensor-examples-review01','--setenv=QT_QPA_PLATFORM=wayland','--setenv=WAYLAND_DISPLAY='+sockets[0],'/usr/local/bin/f8-sensors'],env=env,capture_output=True,text=True,timeout=10);assert p.returncode==0,p.stderr
time.sleep(3)
print(json.dumps({'launch_requested':True,'status':subprocess.run(['systemctl','--user','show','f8-sensor-examples-review01','-p','ActiveState','-p','SubState'],env=env,capture_output=True,text=True).stdout,'logs':subprocess.run(['journalctl','--user','-u','f8-sensor-examples-review01','-n','15','--no-pager'],env=env,capture_output=True,text=True).stdout},indent=2))
PY
