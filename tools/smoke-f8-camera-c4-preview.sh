#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess,time
from pathlib import Path
assert os.getuid()==1601
env={**os.environ,'XDG_RUNTIME_DIR':'/run/user/1601','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus',
 'QT_QPA_PLATFORM':'wayland'}
sockets=[p.name for p in Path('/run/user/1601').glob('wayland-*') if p.is_socket()];assert sockets
env['WAYLAND_DISPLAY']=sockets[0]
folder=Path('/home/f8test/.cache/f8-camera-aiq-c4-stage')
sample=1
while (folder/f'preview-smoke{sample:02d}.log').exists():sample+=1
snapshot=folder/f'preview-smoke{sample:02d}.png';assert not snapshot.exists()
log=folder/f'preview-smoke{sample:02d}.log'
with log.open('w') as output:
 p=subprocess.Popen(['/usr/local/bin/f8-camera-preview','--autostart','--quit-after','14','--snapshot',str(snapshot)],env=env,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
 try:code=p.wait(timeout=23)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,15)
  try:code=p.wait(timeout=4)
  except subprocess.TimeoutExpired:os.killpg(p.pid,9);code=p.wait(timeout=3)
state=Path('/run/user/1601/f8-camera-preview-status.json')
status=json.loads(state.read_text()) if state.exists() else None
print(json.dumps({'exit':code,'status':status,'snapshot_exists':snapshot.exists(),'snapshot_path':str(snapshot),
 'log':log.read_text(errors='replace')[-5000:]},indent=2))
PY
