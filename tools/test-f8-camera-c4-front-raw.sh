#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='532eb6df-13ce-4e63-9645-24d4136d96b9'
def run(args,timeout=10):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
        return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except subprocess.TimeoutExpired as e:return {'timeout':True,'stderr':(e.stderr or b'').decode(errors='replace')}
out={}
out['users']=run(['fuser','/dev/video0','/dev/video11','/dev/video22','/dev/video31'])
assert not out['users']['stdout'].strip(),out['users']
out['front_controls']=run(['v4l2-ctl','-d','/dev/v4l-subdev2','--all','--list-ctrls'])
out['back_controls']=run(['v4l2-ctl','-d','/dev/v4l-subdev5','--all','--list-ctrls'])
target=Path('/run/f8-camera-c4/front-2592x1944.raw');assert not target.exists()
out['capture']=run(['v4l2-ctl','-d','/dev/video0','--set-fmt-video=width=2592,height=1944,pixelformat=RG10',
 '--get-fmt-video','--stream-mmap=3','--stream-poll','--stream-count=2','--stream-to='+str(target)],12)
out['bytes']=target.stat().st_size if target.exists() else None
out['diagnostics']=run(['sh','-c','for p in /proc/rkcif*; do test -f "$p" && echo "$p" && cat "$p"; done; dmesg | tail -85'])
print(json.dumps(out,indent=2))
PY
