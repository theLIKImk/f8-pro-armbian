#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess,time
from pathlib import Path
assert os.getuid()==1601
env={**os.environ,'XDG_RUNTIME_DIR':'/run/user/1601','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus'}
sockets=[p.name for p in Path('/run/user/1601').glob('wayland-*') if p.is_socket()];assert sockets
p=subprocess.run(['systemd-run','--user','--collect','--unit=f8-kamoso-review01',
 '--setenv=QT_QPA_PLATFORM=wayland','--setenv=WAYLAND_DISPLAY='+sockets[0],'/usr/local/bin/f8-kamoso'],
 env=env,capture_output=True,text=True,timeout=12)
assert p.returncode==0,p.stderr
time.sleep(4)
logs=sorted((Path.home()/'.cache/f8-kamoso').glob('*.log'),key=lambda p:p.stat().st_mtime)
print(json.dumps({'launch_requested':True,'status':subprocess.run(['systemctl','--user','show','f8-kamoso-review01','-p','ActiveState','-p','SubState'],env=env,capture_output=True,text=True).stdout,
 'latest_log':str(logs[-1]) if logs else None,'log_tail':logs[-1].read_text(errors='replace')[-7000:] if logs else ''},indent=2))
PY
