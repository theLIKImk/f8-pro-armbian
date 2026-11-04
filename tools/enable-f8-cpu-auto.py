import json,os,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
ps=[Path('/sys/devices/system/cpu/cpufreq/policy'+str(n)) for n in [0,4,6]]
assert all((p/'scaling_driver').read_text().strip()=='f8-p2-fixedvolt' for p in ps)
out={'samples':[]};children=[];ok=False
try:
 for p in ps:
  assert (p/'scaling_min_freq').read_text().strip()=='816000' and (p/'scaling_max_freq').read_text().strip()=='1200000'
  (p/'scaling_governor').write_text('ondemand')
 for cpu in [0,4,6]:children.append(subprocess.Popen(['taskset','-c',str(cpu),'/usr/bin/python3','-I','-c','import time;stop=time.monotonic()+2\nwhile time.monotonic()<stop:sum(range(10000))'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
 for i in range(20):
  out['samples'].append({'phase':'load' if any(c.poll() is None for c in children) else 'idle','khz':{p.name:int((p/'scaling_cur_freq').read_text()) for p in ps}});time.sleep(.25)
 for c in children:assert c.wait(timeout=1)==0
 for p in ps:assert any(s['khz'][p.name]>816000 for s in out['samples'] if s['phase']=='load'),p.name
 ok=True
finally:
 for c in children:
  if c.poll() is None:c.kill();c.wait(timeout=2)
 if not ok:
  for p in ps:(p/'scaling_governor').write_text('powersave')
out['auto_verified']=ok;out['final']={p.name:{n:(p/n).read_text().strip() for n in ['scaling_governor','scaling_cur_freq','scaling_min_freq','scaling_max_freq']} for p in ps}
print(json.dumps(out,indent=2))
