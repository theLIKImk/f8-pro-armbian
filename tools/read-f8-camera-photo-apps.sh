#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=25)
 return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'policy':run(['apt-cache','policy','kamoso','guvcview','webcamoid','plasma-camera']),
 'kamoso_simulation':run(['apt-get','-s','--no-install-recommends','--no-upgrade','install','kamoso']),
 'camera_users':run(['fuser','/dev/video22','/dev/video29','/dev/video30']),
 'programs':run(['sh','-c','command -v kamoso; command -v guvcview; command -v ffmpeg; true'])},indent=2))
PY
