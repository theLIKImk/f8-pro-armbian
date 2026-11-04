#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
def run(args):
 try:
  p=subprocess.run(args,capture_output=True,text=True,timeout=8);return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 except Exception as e:return {'error':str(e)}
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'kernel':run(['dmesg']),
 'system':run(['systemctl','is-system-running']),
 'failed':run(['systemctl','--failed','--no-legend','--no-pager']),
 'gki':run(['sh','-c',"grep -E 'CONFIG_NO_GKI|CONFIG_OF_DYNAMIC|CONFIG_OF_OVERLAY' /boot/config-$(uname -r)"]),
 'app':run(['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','systemctl','--user','status','f8-camera-test','--no-pager'])},indent=2))
PY
