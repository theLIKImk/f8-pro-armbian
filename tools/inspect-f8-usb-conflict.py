import json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
o={}
for k,a in [('kernel_context',['journalctl','-k','-b','--no-pager','-n','550']),('failed',['systemctl','--failed','--no-legend','--no-pager']),('gpio',['cat','/sys/kernel/debug/gpio'])]:
 r=subprocess.run(a,capture_output=True,text=True,timeout=12)
 if k=='kernel_context':
  ls=r.stdout.splitlines(); indices=set()
  for i,l in enumerate(ls):
   if any(x in l.lower() for x in ['f8-otg','6-006a','6-0022','gpio','busy','regulator','defer']):indices.update(range(max(0,i-3),min(len(ls),i+4)))
  r.stdout='\n'.join(ls[i] for i in sorted(indices))
 o[k]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
for f in ['/sys/kernel/debug/devices_deferred','/sys/kernel/debug/regulator/regulator_summary']:
 try:o[f]=Path(f).read_text()
 except OSError as e:o[f]=str(e)
print(json.dumps(o,indent=2))
