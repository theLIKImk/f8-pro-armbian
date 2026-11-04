#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
out={}
for n,args in {'processes':['pgrep','-af','maliit|feedbackd|f8-cover'],'packages':['sh','-c','dpkg-query -W "*maliit*" "*feedback*" 2>/dev/null'],'qml':['sh','-c','find /usr/share/maliit /usr/lib/aarch64-linux-gnu/maliit -type f 2>/dev/null | head -65'],'config':['sh','-c','gsettings list-recursively org.maliit.keyboard.maliit 2>/dev/null; cat ~/.config/maliit.org/server.conf 2>/dev/null; true']}.items():
 p=subprocess.run(args,capture_output=True,text=True,timeout=12);out[n]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps(out,indent=2))
PY
