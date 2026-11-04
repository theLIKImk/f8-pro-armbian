#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
assert Path('/sys/firmware/devicetree/base/chosen/f8-camera-trial').read_bytes()==b'c1\0'
for name in ['fdcb0000.rkisp','fdcc0000.rkisp']:
    p=Path('/sys/bus/platform/devices')/name/'driver';assert p.exists() and p.resolve().name=='rkisp_hw',(name,str(p.resolve()))
result={}
for name in ['rkisp0-vir0','rkisp1-vir0']:
    p=Path('/sys/bus/platform/devices')/name/'driver'
    before=p.exists()
    if not before:Path('/sys/bus/platform/drivers_probe').write_text(name+'\n')
    result[name]={'before_bound':before,'after_driver':p.resolve().name if p.exists() else None}
result['pending']=subprocess.run(['sh','-c','find /sys/kernel/debug -maxdepth 3 -iname "*pending*" -o -iname "*async*"'],capture_output=True,text=True,timeout=10).stdout
result['logs']=subprocess.run(['sh','-c','dmesg | tail -45'],capture_output=True,text=True,timeout=10).stdout
print(json.dumps(result,indent=2))
PY
