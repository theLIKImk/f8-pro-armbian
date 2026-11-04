#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
assert Path('/sys/firmware/devicetree/base/chosen/f8-camera-async-trial').read_bytes()==b'c4\0'
out={}
for node in ['/dev/video0','/dev/video11','/dev/video22','/dev/video31']:
    p=subprocess.run(['v4l2-ctl','-d',node,'--all','--list-formats-ext'],capture_output=True,text=True,timeout=10)
    out[node]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'nodes':out},indent=2))
PY
