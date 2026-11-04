#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess
from pathlib import Path
out={}
for n,args in {'candidate':['apt-cache','policy','feedbackd','feedbackd-device-themes'],'simulation':['apt-get','-s','--no-install-recommends','--no-upgrade','install','feedbackd'],'keyboard_config':['sh','-c','cat ~/.config/plasmakeyboardrc 2>/dev/null; true'],'bus':['sh','-c','busctl --user --list --no-pager | grep -E "Feedback|keyboard" || true'],'udev':['udevadm','info','--query=property','--name=/dev/input/f8-haptic']}.items():
 p=subprocess.run(args,capture_output=True,text=True,timeout=18);out[n]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps(out,indent=2))
PY
