import json,os,subprocess
from pathlib import Path
assert os.geteuid()==0
w=Path('/var/tmp/f8-pro-ksystemstats-k1');s=w/'status.json'
r=subprocess.run(['systemctl','show','f8-ksystemstats-build.service','-p','ActiveState','-p','SubState','-p','ExecMainStatus'],capture_output=True,text=True,timeout=8)
status=json.loads(s.read_text()) if s.exists() else None
if status and 'tail' in status:status.pop('tail');status['error']=status.get('error','')[:200]
lines=(w/'build.log').read_text().splitlines() if (w/'build.log').exists() else []
errors=[x[:350] for x in lines if any(k in x for k in ['error:','fatal error','undefined reference','Unknown option'])][-12:]
print(json.dumps({'status':status,'unit':r.stdout,'diagnostics':errors},indent=2))
