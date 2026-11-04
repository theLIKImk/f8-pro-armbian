#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess
from pathlib import Path
assert os.getuid()==1601
folder=Path.home()/'.cache/f8-sensor-examples02';assert not folder.exists();folder.mkdir()
env={**os.environ,'XDG_RUNTIME_DIR':'/run/user/1601','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus','QT_QPA_PLATFORM':'offscreen'}
out={}
for tab,name in [(0,'examples'),(1,'raw')]:
 png=folder/(name+'.png');state=folder/(name+'.json')
 p=subprocess.run(['/usr/local/bin/f8-sensors','--preview',str(png),'--preview-tab',str(tab),'--status-json',str(state)],env=env,capture_output=True,text=True,timeout=18)
 out[name]={'exit':p.returncode,'stderr':p.stderr[-2500:],'png_bytes':png.stat().st_size if png.exists() else 0,'state':json.loads(state.read_text()) if state.exists() else None}
print(json.dumps(out,indent=2))
PY
