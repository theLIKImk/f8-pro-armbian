import json,subprocess
from pathlib import Path
path=Path('/var/lib/f8-pro/touch-rate/p128-2/result.json')
if path.exists():
 data=json.loads(path.read_text());out={'measurement':{k:v for k,v in data.items() if k not in ['frames','irq_timestamps']}}
 r=subprocess.run(['/usr/bin/python3','/var/lib/f8-pro/touch-rate/p128-load2/restore.py'],capture_output=True,text=True,timeout=35)
 out['restore']={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 if r.returncode==0:subprocess.run(['systemctl','stop','f8-touch-rate-rollback-p128-2.timer'],check=True,timeout=8)
 print(json.dumps(out,indent=2));assert r.returncode==0
else:
 print(Path('/run/f8-touch-rate-p128-2.json').read_text())
