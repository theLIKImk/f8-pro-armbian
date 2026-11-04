import json,subprocess
from pathlib import Path
w=Path('/var/tmp/f8-pro-kwin-touch-k2');o={}
p=w/'status.json';o['status']=json.loads(p.read_text()) if p.exists() else None
o['log_tail']=(w/'build.log').read_text()[-3500:] if (w/'build.log').exists() else None
o['unit']=subprocess.run(['systemctl','show','f8-kwin-touch-build','-p','ActiveState','-p','SubState','-p','Result'],capture_output=True,text=True,timeout=8).stdout
print(json.dumps(o))
