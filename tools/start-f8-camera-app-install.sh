#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
unit='f8-camera-app-install'
exists=subprocess.run(['systemctl','show',unit,'-p','LoadState','--value'],capture_output=True,text=True).stdout.strip()
assert exists=='not-found',('Check existing package task before rerun',exists)
p=subprocess.run(['apt-cache','policy','qv4l2','gstreamer1.0-tools'],capture_output=True,text=True,timeout=15)
assert p.returncode==0 and '(none)' not in '\n'.join(s for s in p.stdout.splitlines() if 'Candidate:' in s),p.stdout
command=['systemd-run','--no-block','--unit='+unit,'--property=Type=oneshot','--property=RemainAfterExit=yes',
 '--setenv=DEBIAN_FRONTEND=noninteractive','/usr/bin/apt-get','-y','--no-remove','--no-install-recommends','install','qv4l2','gstreamer1.0-tools']
r=subprocess.run(command,capture_output=True,text=True,timeout=15);assert r.returncode==0,r.stderr
print(json.dumps({'unit':unit,'started':True,'candidate_policy':p.stdout,'result':r.stderr},indent=2))
PY
