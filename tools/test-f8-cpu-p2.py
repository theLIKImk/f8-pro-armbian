import json,os,re,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
base=Path('/sys/devices/system/cpu/cpufreq');policies=[base/('policy'+str(n)) for n in [0,4,6]]
assert all((p/'scaling_driver').read_text().strip()=='f8-p2-fixedvolt' for p in policies)
assert all((p/'scaling_governor').read_text().strip()=='powersave' for p in policies)
zone=next(p for p in Path('/sys/class/thermal').glob('thermal_zone*') if (p/'type').read_text().strip()=='soc-thermal')
out={'runs':[],'samples':[]};initial={str(p):{n:(p/n).read_text().strip() for n in ['scaling_governor','scaling_min_freq','scaling_max_freq']} for p in policies}
restore='from pathlib import Path;d='+repr(initial)+';[(Path(p,n).write_text(v)) for p,a in d.items() for n,v in a.items()]'
unit='f8-cpu-p2-restore-'+str(int(time.time()))
subprocess.run(['systemd-run','--quiet','--unit='+unit,'--on-active=60s','/usr/bin/python3','-c',restore],check=True,capture_output=True,timeout=8)
worker="import json,time\nx=1;n=0;t=time.monotonic();stop=t+2\nwhile time.monotonic()<stop:\n for i in range(10000):x=(x*1664525+1013904223)&0xffffffff\n n+=10000\nprint(json.dumps({'iterations':n,'seconds':time.monotonic()-t,'checksum':x}))"
proc=None;started=time.monotonic()
def regulators():
 return {(p/'name').read_text().strip():(p/'microvolts').read_text().strip() for p in Path('/sys/class/regulator').glob('*') if (p/'name').exists() and (p/'name').read_text().startswith('vdd_cpu')}
out['volts_before']=regulators()
try:
 for cpu,p in zip([0,4,6],policies):
  (p/'scaling_governor').write_text('userspace')
  for freq in [816000,1008000,1200000]:
   assert int((zone/'temp').read_text())<65000
   (p/'scaling_setspeed').write_text(str(freq));time.sleep(.2)
   observed=int((p/'scaling_cur_freq').read_text());assert observed==freq,(cpu,freq,observed)
   clk=Path('/sys/kernel/debug/clk/clk_summary').read_text();actual=[s for s in clk.splitlines() if 'scmi_clk_cpu' in s]
   proc=subprocess.Popen(['taskset','-c',str(cpu),'/usr/bin/python3','-I','-c',worker],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   while proc.poll() is None:
    temp=int((zone/'temp').read_text());out['samples'].append({'cpu':cpu,'khz':freq,'temp_mc':temp})
    if temp>=65000 or time.monotonic()-started>48:raise RuntimeError('CPU bounded test stopped at temperature/time limit')
    time.sleep(.5)
   stdout,stderr=proc.communicate(timeout=2);assert proc.returncode==0,stderr;proc=None
   out['runs'].append({'cpu':cpu,'frequency_khz':freq,'observed_khz':observed,'clock_summary':actual,'benchmark':json.loads(stdout),'volts':regulators()})
  (p/'scaling_governor').write_text('powersave')
except Exception as e:out['error']=str(e)
finally:
 if proc is not None:proc.kill();proc.communicate(timeout=3)
 for p,values in initial.items():
  for n,v in values.items():Path(p,n).write_text(v)
 subprocess.run(['systemctl','stop',unit+'.timer'],capture_output=True,timeout=8)
out['volts_after']=regulators();out['max_temp_celsius']=max(x['temp_mc'] for x in out['samples'])/1000 if out['samples'] else None
out['restored']={p.name:{n:(p/n).read_text().strip() for n in ['scaling_governor','scaling_cur_freq','scaling_min_freq','scaling_max_freq']} for p in policies}
log=subprocess.run(['journalctl','-k','-b','--no-pager'],capture_output=True,text=True,timeout=10).stdout
out['faults']=[s for s in log.splitlines() if re.search(r'\bOops:|\bBUG:|rcu.*stall|watchdog.*lockup',s,re.I)]
print(json.dumps(out,indent=2))
