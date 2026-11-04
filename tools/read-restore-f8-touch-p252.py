import json,subprocess
from pathlib import Path
W=Path('/var/lib/f8-pro/touch-rate')
out={}
try:
 r=json.loads((W/'p252-1/result.json').read_text())
 out['measurement']={k:v for k,v in r.items() if k not in ['frames','irq_timestamps']}
finally:
 r=subprocess.run(['/usr/bin/python3',str(W/'p252-load/restore.py')],capture_output=True,text=True,timeout=35)
 out['restore']={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 if r.returncode==0:subprocess.run(['systemctl','stop','f8-touch-rate-rollback-p252.timer'],check=True,timeout=8)
 print(json.dumps(out,indent=2))
 assert r.returncode==0
