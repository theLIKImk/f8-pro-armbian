#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
folder=Path('/home/f8test/.cache/f8-camera-aiq-c4-stage')
out={'logs':{p.name:p.read_text(errors='replace')[-6000:] for p in folder.glob('preview-smoke*.log')}}
state=Path('/run/user/1601/f8-camera-preview-status.json')
out['state']=json.loads(state.read_text()) if state.exists() else None
out['processes']=subprocess.run(['pgrep','-af','camera-preview.py|aiq-backend.py|v4l2-ctl.*stream-to=-'],capture_output=True,text=True).stdout
print(json.dumps(out,indent=2))
PY
