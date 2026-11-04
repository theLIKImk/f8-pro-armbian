#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
logs=sorted((Path.home()/'.cache/f8-kamoso').glob('*.log'),key=lambda p:p.stat().st_mtime)
out={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'log':logs[-1].read_text(errors='replace')[-10000:] if logs else ''}
for name,args in {'processes':['pgrep','-af','kamoso|aiq-backend|v4l2-ctl'],'capture':['fuser','/dev/video22'],'format':['v4l2-ctl','-d','/dev/video22','--get-fmt-video'],'cmdline':['cat','/proc/cmdline'],'ffmpeg':['sh','-c','command -v ffmpeg; command -v ffprobe']}.items():
 p=subprocess.run(args,capture_output=True,text=True,timeout=10);out[name]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps(out,indent=2))
PY
