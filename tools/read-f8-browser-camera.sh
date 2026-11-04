#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
state=Path('/run/user/1601/f8-camera-preview-status.json');out={'state':json.loads(state.read_text()) if state.exists() else None}
for name,args in {'processes':['pgrep','-af','chromium|kamoso|gst-launch|aiq-backend|v4l2-ctl'],'users':['fuser','/dev/video42','/dev/video22','/dev/video31'],'format':['v4l2-ctl','-d','/dev/video42','--all'],'version':['sh','-c','command -v chromium; chromium --version']}.items():
 p=subprocess.run(args,capture_output=True,text=True,timeout=12);out[name]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps(out,indent=2))
PY
