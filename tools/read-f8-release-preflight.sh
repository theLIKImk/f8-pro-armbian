#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess,shutil
from pathlib import Path
out={}
for name,args in {
'root':['findmnt','-no','SOURCE,FSTYPE,OPTIONS','/'],
'disk':['df','-h','/'],
'size':['du','-x','-h','--max-depth=1','/usr/local','/etc','/var','/opt'],
'units':['systemctl','cat','f8-live-prepare.service','f8-live-network.service','f8-live-ssh.service','f8-desktop-hardware.service','f8-desktop.target'],
'accounts':['getent','passwd'],
}.items():
 p=subprocess.run(args,text=True,capture_output=True,timeout=25);out[name]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
out['rsync']=shutil.which('rsync')
out['files']={}
for pat in ['/etc/sddm.conf.d/*.conf','/usr/libexec/f8-pro/*prepare*','/usr/libexec/f8-pro/*network*','/usr/libexec/f8-pro/*ssh*','/etc/sudoers.d/*','/home/f8test/.config/systemd/user/*.service','/home/f8test/.config/f8-cover.json']:
 import glob
 for name in glob.glob(pat):
  p=Path(name)
  if p.is_file():out['files'][name]=p.read_text()
print(json.dumps(out,indent=2))
PY
