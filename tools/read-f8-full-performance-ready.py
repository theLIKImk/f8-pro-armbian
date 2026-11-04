import json,os,subprocess,sys
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
sys.path.insert(0,'/usr/local/lib/f8-pro');from performance_state import snapshot
r=subprocess.run(['/usr/local/lib/f8-pro/performance-apply.py','--all-auto'],capture_output=True,text=True,timeout=15)
out={'apply_exit':r.returncode,'apply':r.stdout,'apply_error':r.stderr,'devices':{k:snapshot(k) for k in ['gpu','cpu0','cpu4','cpu6']}}
r=subprocess.run(['systemd-analyze','verify','--man=no','/etc/systemd/system/f8-performance-gpu-start.service','/etc/systemd/system/f8-performance-cpu-start.service'],capture_output=True,text=True,timeout=15)
out['unit_verify']={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
out['startup_links']={n:Path('/etc/systemd/system/f8-desktop.target.wants/'+n).is_symlink() for n in ['f8-performance-gpu-start.service','f8-performance-cpu-start.service']}
print(json.dumps(out,indent=2))
