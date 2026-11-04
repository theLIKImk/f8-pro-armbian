import base64,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];O=P/'outputs/armbian/f8-cpu-p3'
meta=json.loads((O/'module-check.json').read_text());assert meta['actual_image_import_crcs_verified']
data=base64.b64encode((O/'f8-cpufreq-p3.ko').read_bytes()).decode()
code='''import base64,fcntl,hashlib,json,os,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert Path('/proc/device-tree/chosen/f8-cpu-trial').read_bytes()==b'p2-fixedvolt-1200mhz\\0'
b=base64.b64decode(DATA);assert hashlib.sha256(b).hexdigest()==DIGEST
dest=Path('/usr/local/lib/f8-pro/experimental/f8-cpufreq-p3.ko');assert not dest.is_symlink();dest.write_bytes(b);dest.chmod(0o644)
ps=Path('/sys/devices/system/cpu/cpufreq');out={}
with open('/run/lock/f8-performance.lock','w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 assert Path('/sys/module/f8_cpufreq_p2').exists() and not Path('/sys/module/f8_cpufreq_p3').exists()
 for p in ps.glob('policy*'):(p/'scaling_governor').write_text('powersave')
 time.sleep(.5)
 subprocess.run(['rmmod','f8_cpufreq_p2'],check=True,capture_output=True,timeout=12)
 r=subprocess.run(['insmod',str(dest),'max_little_khz=1200000','max_big_khz=1200000'],capture_output=True,text=True,timeout=30)
 out['load_exit']=r.returncode;out['stderr']=r.stderr
 out['policies']={p.name:{n:(p/n).read_text().strip() for n in ['scaling_driver','scaling_governor','scaling_available_frequencies','scaling_cur_freq','scaling_min_freq','scaling_max_freq']} for p in ps.glob('policy*')}
 if r.returncode!=0 or len(out['policies'])!=3:
  if Path('/sys/module/f8_cpufreq_p3').exists():subprocess.run(['rmmod','f8_cpufreq_p3'],capture_output=True,timeout=12)
  fallback=subprocess.run(['insmod','/usr/local/lib/f8-pro/experimental/f8-cpufreq-p2.ko'],capture_output=True,text=True,timeout=12)
  out['fallback_exit']=fallback.returncode;out['fallback_stderr']=fallback.stderr
  for p in ps.glob('policy*'):(p/'scaling_governor').write_text('ondemand')
out['kernel_tail']=subprocess.run(['journalctl','-k','-b','-n','75','--no-pager'],capture_output=True,text=True,timeout=10).stdout
out['regulators']={}
for p in Path('/sys/class/regulator').glob('*'):
 if (p/'name').exists() and (p/'name').read_text().startswith('vdd_cpu'):out['regulators'][(p/'name').read_text().strip()]=(p/'microvolts').read_text().strip()
print(json.dumps(out,indent=2))
'''.replace('DATA',repr(data)).replace('DIGEST',repr(meta['module_sha256']))
(P/'local/hardware/cpu-p3-trial-runner.py').write_text(code)
