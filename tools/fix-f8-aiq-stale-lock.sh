#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,stat,subprocess
from pathlib import Path
p=Path('/tmp/aiq0.lock')
s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and s.st_size<4096
users=subprocess.run(['fuser',str(p)],capture_output=True,text=True,timeout=5)
assert users.returncode==1 and not users.stdout.strip(),(users.stdout,users.stderr)
assert p.resolve()==p
p.unlink()
print(json.dumps({'removed_stale_root_trial_lock':str(p),'active_users':False,'global_permissions_changed':False}))
PY
