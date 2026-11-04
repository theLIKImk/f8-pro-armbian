"""Read only the diagnostic's own data, preserving full traces for offline analysis."""
import json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
folder=Path('/var/lib/f8-pro/touch-diagnostic/r2')
out={'summary':json.loads((folder/'summary.json').read_text())}
for name,p in [('kernel_frames',folder/'frames.jsonl'),('application_events',Path('/home/likimk/.cache/f8-multitouch-test/trace-r2.jsonl'))]:
 out[name]=[json.loads(line) for line in p.read_text().splitlines() if line] if p.exists() else []
r=subprocess.run(['systemctl','show','f8-touch-capture-r2.service','-p','ActiveState','-p','Result'],capture_output=True,text=True,timeout=8)
out['unit']=r.stdout
print(json.dumps(out))
