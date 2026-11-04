#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
out={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
state=Path('/run/user/1601/f8-camera-preview-status.json');out['preview_state']=json.loads(state.read_text()) if state.exists() else None
for name,args in {'front_media':['media-ctl','-p','-d','/dev/media3'],'front_controls':['v4l2-ctl','-d','/dev/v4l-subdev2','--all','--list-ctrls'],'front_formats':['v4l2-ctl','-d','/dev/video31','--all','--list-formats-ext'],'users':['fuser','/dev/video22','/dev/video31','/dev/video0'],'camera_service':['systemctl','status','f8-camera-start.service','--no-pager']}.items():
 p=subprocess.run(args,capture_output=True,text=True,timeout=15);out[name]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps(out,indent=2))
PY
