#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
assert Path('/sys/firmware/devicetree/base/chosen/f8-camera-async-trial').read_bytes()==b'c4\0'
cmd=['apt-get','--no-install-recommends','--no-upgrade','install','kamoso']
sim=subprocess.run(cmd[:1]+['-s']+cmd[1:],capture_output=True,text=True,timeout=25)
assert sim.returncode==0,sim.stderr
inst=[s.split()[1] for s in sim.stdout.splitlines() if s.startswith('Inst ')]
assert set(inst)<={'kamoso','gstreamer1.0-qt6'},inst
assert not any(s.startswith('Remv ') for s in sim.stdout.splitlines()),sim.stdout
p=subprocess.run(cmd[:1]+['-y']+cmd[1:],capture_output=True,text=True,timeout=55,
 env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','DEBIAN_FRONTEND':'noninteractive'})
assert p.returncode==0,(p.stdout,p.stderr)
print(json.dumps({'new_packages':inst,'stdout':p.stdout,'stderr':p.stderr,
 'versions':subprocess.check_output(['dpkg-query','-W','kamoso','gstreamer1.0-qt6'],text=True)},indent=2))
PY
