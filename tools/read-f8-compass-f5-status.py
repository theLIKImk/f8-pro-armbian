import subprocess,json,time,hashlib
from pathlib import Path
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
p=Path('/home/likimk/.config/f8-pro/compass-calibration.json');c=json.loads(p.read_text())
o={'processes':run(['pgrep','-u','1602','-af','compass']),'calibration':{'version':c.get('version'),'method':c.get('method'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},'status':None}
s=Path('/run/user/1602/f8-compass-status.json')
if s.exists():o['status']=json.loads(s.read_text())
print(json.dumps(o))
