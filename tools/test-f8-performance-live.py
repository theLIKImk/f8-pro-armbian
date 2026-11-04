import base64,json,os,subprocess,sys
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
sys.path.insert(0,'/usr/local/lib/f8-pro');from performance_state import snapshot
cmd=['/usr/local/lib/f8-pro/performance-apply.py'];out={'tests':[]}
try:
 for key,freq in [('gpu',300000000),('cpu0',1008000)]:
  r=subprocess.run(cmd+['--device',key,'--mode','fixed','--minimum',str(freq),'--maximum',str(freq)],capture_output=True,text=True,timeout=10)
  d=json.loads(r.stdout);assert r.returncode==0 and d['ok'],(r.stdout,r.stderr)
  s=snapshot(key);assert s['minimum']==s['maximum']==freq
  out['tests'].append({'key':key,'fixed_target':freq,'state':s})
  r=subprocess.run(cmd+['--device',key,'--mode','auto'],capture_output=True,text=True,timeout=10);assert r.returncode==0,r.stdout
 before=snapshot('gpu')
 r=subprocess.run(cmd+['--device','gpu','--mode','fixed','--minimum','1000000000','--maximum','1000000000'],capture_output=True,text=True,timeout=10)
 after=snapshot('gpu');assert r.returncode!=0 and (before['minimum'],before['maximum'])==(after['minimum'],after['maximum'])
 out['unvalidated_1ghz_rejected_without_writes']=True
finally:
 r=subprocess.run(cmd+['--all-auto'],capture_output=True,text=True,timeout=15);out['restored']=json.loads(r.stdout);assert r.returncode==0,r.stdout
out['panel_png']=base64.b64encode(Path('/home/likimk/.cache/f8-performance-panel.png').read_bytes()).decode()
print(json.dumps(out))
