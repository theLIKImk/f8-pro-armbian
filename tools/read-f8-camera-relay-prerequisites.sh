#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
out={}
for name,args in {'kernel':['uname','-r'],'module':['modinfo','v4l2loopback'],'headers':['sh','-c','readlink -f /lib/modules/$(uname -r)/build; test -s /lib/modules/$(uname -r)/build/Module.symvers'],'nodes':['sh','-c','ls /dev/video*; ls /sys/class/video4linux/*/name | head -2'],'state':['cat','/run/user/1601/f8-camera-preview-status.json']}.items():
 p=subprocess.run(args,capture_output=True,text=True,timeout=12);out[name]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps(out,indent=2))
PY
