#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,signal,subprocess,time
from pathlib import Path
assert os.getuid()==1601
runtime=Path('/run/user/1601');state=json.loads((runtime/'f8-camera-preview-status.json').read_text())
assert not state['engine_pid'] and not state['capture_pid'],'Do not interrupt resumed capture'
record=subprocess.run(['pgrep','-u','1601','-af','gst-launch-1.0.*avimux'],capture_output=True,text=True);assert not record.stdout.strip(),'Preserve recording'
pids=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  if p.stat().st_uid!=os.getuid():continue
  args=(p/'cmdline').read_bytes().split(b'\0')
  if b'/usr/local/lib/f8-pro/camera-preview.py' in args:pids.append(int(p.name))
 except (OSError,PermissionError):pass
assert len(pids)==1,pids
os.kill(pids[0],signal.SIGTERM)
for _ in range(40):
 p=subprocess.run(['fuser','/dev/video42'],capture_output=True,text=True)
 if not p.stdout.strip():break
 time.sleep(.1)
assert not p.stdout.strip(),'Preserve remaining virtual camera consumers'
env={**os.environ,'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus'}
sockets=[p.name for p in runtime.glob('wayland-*') if p.is_socket()];assert sockets
p=subprocess.run(['systemd-run','--user','--collect','--unit=f8-camera-browser-review01','--setenv=QT_QPA_PLATFORM=wayland','--setenv=WAYLAND_DISPLAY='+sockets[0],'/usr/local/bin/f8-camera-preview','--camera',state['camera'],'--autostart','--relay'],env=env,capture_output=True,text=True,timeout=10);assert p.returncode==0,p.stderr
time.sleep(4)
print(json.dumps(json.loads((runtime/'f8-camera-preview-status.json').read_text()),indent=2))
PY
