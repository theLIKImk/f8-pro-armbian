#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
sim=subprocess.run(['apt-get','-s','--no-install-recommends','--no-upgrade','install','strace'],capture_output=True,text=True,timeout=20)
assert sim.returncode==0,sim.stderr
inst=[s.split()[1] for s in sim.stdout.splitlines() if s.startswith('Inst ')]
assert set(inst)<= {'strace'},inst
assert not any(s.startswith('Remv ') for s in sim.stdout.splitlines())
p=subprocess.run(['apt-get','-y','--no-install-recommends','--no-upgrade','install','strace'],capture_output=True,text=True,timeout=55,
 env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','DEBIAN_FRONTEND':'noninteractive'})
assert p.returncode==0,(p.stdout,p.stderr)
print(json.dumps({'installed':inst,'stdout':p.stdout,'stderr':p.stderr},indent=2))
PY
