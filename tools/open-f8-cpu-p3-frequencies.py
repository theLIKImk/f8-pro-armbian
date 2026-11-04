import fcntl,hashlib,json,os,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert Path('/sys/module/f8_cpufreq_p3').exists()
p=Path('/usr/local/lib/f8-pro/experimental/f8-cpufreq-p3.ko');assert hashlib.sha256(p.read_bytes()).hexdigest()=='35461712ee2e7d827163ae208ce1f3301a7b082f3a7a26d5cba5a508f55c1196'
with open('/run/lock/f8-performance.lock','w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 for policy in Path('/sys/devices/system/cpu/cpufreq').glob('policy*'):(policy/'scaling_governor').write_text('powersave')
 time.sleep(.5);subprocess.run(['rmmod','f8_cpufreq_p3'],check=True,capture_output=True,timeout=15)
 r=subprocess.run(['insmod',str(p),'max_little_khz=1800000','max_big_khz=2400000'],capture_output=True,text=True,timeout=30)
 out={'load_exit':r.returncode,'stderr':r.stderr,'policies':{}}
 for policy in Path('/sys/devices/system/cpu/cpufreq').glob('policy*'):
  out['policies'][policy.name]={n:(policy/n).read_text().strip() for n in ['scaling_driver','scaling_governor','scaling_available_frequencies','scaling_cur_freq','scaling_max_freq']}
 if r.returncode!=0:
  fallback=subprocess.run(['insmod','/usr/local/lib/f8-pro/experimental/f8-cpufreq-p2.ko'],capture_output=True,text=True,timeout=15)
  out['fallback_exit']=fallback.returncode;out['fallback_stderr']=fallback.stderr
print(json.dumps(out,indent=2))
