#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,re,subprocess
simulation=subprocess.run(['apt-get','-s','--no-install-recommends','--no-upgrade','install','feedbackd'],capture_output=True,text=True,timeout=20)
assert simulation.returncode==0 and '0 upgraded, 6 newly installed, 0 to remove' in simulation.stdout,simulation.stdout
p=subprocess.run(['apt-get','-y','--no-install-recommends','--no-upgrade','install','feedbackd'],env={**os.environ,'DEBIAN_FRONTEND':'noninteractive'},capture_output=True,text=True,timeout=70)
print(json.dumps({'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2));assert p.returncode==0
PY
