#!/bin/sh
set -eu
python3 -I - <<'PY'
import configparser,json,subprocess
from pathlib import Path
out={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
c=configparser.ConfigParser(strict=False);c.read(Path.home()/'.config/kwinrc');out['wayland']=dict(c['Wayland']) if c.has_section('Wayland') else {}
for n,args in {'processes':['pgrep','-af','keyboard|kwin_wayland|onboard|wvkbd|squeek'],'packages':['sh','-c','dpkg-query -W "*keyboard*" "*feedback*" 2>/dev/null | head -60'],'entry':['sh','-c','ls /usr/share/applications/*keyboard* /usr/local/share/applications/*keyboard* 2>/dev/null'],'haptic':['sh','-c','ls -l /dev/input/f8-haptic; cat /sys/devices/platform/f8-cover-haptic/motor_active']}.items():
 p=subprocess.run(args,capture_output=True,text=True,timeout=12);out[n]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps(out,indent=2))
PY
