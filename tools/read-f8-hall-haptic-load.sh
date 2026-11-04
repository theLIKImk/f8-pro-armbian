#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
out={}
for name,args in {'log':['sh','-c','dmesg | tail -80'],'gpio':['cat','/sys/kernel/debug/gpio'],'controller':['sh','-c','for p in /sys/bus/gpio/devices/gpiochip*; do echo "$p"; cat "$p/label"; readlink -f "$p/device"; done'],'input':['cat','/proc/bus/input/devices']}.items():
 p=subprocess.run(args,capture_output=True,text=True,timeout=10);out[name]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps(out,indent=2))
PY
