#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess
from pathlib import Path
env={**os.environ,'XDG_RUNTIME_DIR':'/run/user/1601','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus','QT_QPA_PLATFORM':'offscreen'}
out={}
for name,args in {'kscreen':['kscreen-doctor','--help'],'python_evdev':['python3','-c','import evdev;print(evdev.__version__ if hasattr(evdev,"__version__") else "available")'],'tools':['sh','-c','command -v qdbus6; command -v systemd-inhibit; command -v evtest'],'inhibitors':['systemd-inhibit','--list','--no-pager']}.items():
 p=subprocess.run(args,capture_output=True,text=True,timeout=10,env=env);out[name]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps(out,indent=2))
PY
