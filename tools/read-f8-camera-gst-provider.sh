#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
out={}
for name,args in {'udev':['udevadm','info','--query=property','--name=/dev/video22'],
 'provider':['gst-inspect-1.0','video4linux2'],
 'permissions':['sh','-c','ls -l /dev/dma_heap /dev/dma_heap/* /dev/media* /dev/video22 2>/dev/null; true']}.items():
 p=subprocess.run(args,capture_output=True,text=True,timeout=12);out[name]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps(out,indent=2))
PY
