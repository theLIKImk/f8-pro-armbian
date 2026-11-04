#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
assert not Path('/sys/bus/i2c/devices/3-000f').exists()
p=subprocess.run(['i2ctransfer','-y','3','w1@0x0f','0x00','r16'],capture_output=True,text=True,timeout=10)
data={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
if p.returncode==0:
    raw=bytes(int(n,16) for n in p.stdout.split())
    data.update(raw_xyz=[int.from_bytes(raw[n:n+2],'little',signed=True) for n in [3,5,7]],st1=raw[2],st2=raw[9],control=raw[10],astc=raw[12])
print(json.dumps(data,indent=2))
PY
