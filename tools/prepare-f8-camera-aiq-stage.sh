#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,pwd,os
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='532eb6df-13ce-4e63-9645-24d4136d96b9'
p=Path('/home/f8test/.cache/f8-camera-aiq-c4-stage');assert not p.exists()
p.mkdir(mode=0o700,parents=True);u=pwd.getpwnam('f8test');os.chown(p,u.pw_uid,u.pw_gid)
assert not Path('/opt/f8-pro-camera/aiq-v6-c4').exists()
print(json.dumps({'stage':str(p),'root_aiq_installed':False}))
PY
