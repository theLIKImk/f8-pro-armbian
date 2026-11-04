import hashlib,json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
p=Path('/home/likimk/.cache/f8-multitouch-test/results.json');out={'result':json.loads(p.read_text()) if p.exists() else None}
for name,args in [('input_errors',['journalctl','-k','-b','--no-pager','--grep','gsl|touch|i2c|input','-n','80']),('app_errors',['journalctl','-b','--no-pager','--grep','multitouch|QTouch|touch.*discard|never started','-n','40']),('module',['modinfo','/usr/libexec/f8-pro/f8_gsl_shuping.ko'])]:
 r=subprocess.run(args,capture_output=True,text=True,timeout=12);out[name]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
f=Path('/usr/libexec/f8-pro/f8_gsl_shuping.ko');out['module_sha256']=hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None
print(json.dumps(out,indent=2))
