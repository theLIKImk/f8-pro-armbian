#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess,time
from pathlib import Path
assert os.getuid()==1601
runtime=Path('/run/user/1601');sockets=[p.name for p in runtime.glob('wayland-*') if p.is_socket()];assert sockets
env={**os.environ,'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus'}
common=['systemd-run','--user','--collect','--setenv=QT_QPA_PLATFORM=wayland','--setenv=WAYLAND_DISPLAY='+sockets[0]]
p=subprocess.run([*common,'--unit=f8-camera-preview-review01','/usr/local/bin/f8-camera-preview','--camera','front','--autostart','--relay'],env=env,capture_output=True,text=True,timeout=10);assert p.returncode==0,p.stderr
state={}
for _ in range(100):
 try:state=json.loads((runtime/'f8-camera-preview-status.json').read_text())
 except (OSError,ValueError):state={}
 if state.get('relay_running') and state.get('relay_frames',0)>=14:break
 time.sleep(.1)
assert state.get('relay_running') and state.get('relay_frames',0)>=14,state
p=subprocess.run([*common,'--unit=f8-kamoso-review01','/usr/local/bin/f8-kamoso'],env=env,capture_output=True,text=True,timeout=10);assert p.returncode==0,p.stderr
time.sleep(5)
logs=sorted((Path.home()/'.cache/f8-kamoso').glob('relay-*.log'),key=lambda p:p.stat().st_mtime)
out={'state_before_kamoso':state,'state_after_kamoso':json.loads((runtime/'f8-camera-preview-status.json').read_text()),'kamoso_log':logs[-1].read_text(errors='replace')[-4500:] if logs else '',
 'processes':subprocess.run(['pgrep','-af','/usr/bin/kamoso'],capture_output=True,text=True).stdout,'users':subprocess.run(['fuser','/dev/video42'],capture_output=True,text=True).stdout}
print(json.dumps(out,indent=2))
PY
