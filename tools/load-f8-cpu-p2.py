import hashlib,json,os,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert Path('/proc/device-tree/chosen/f8-cpu-trial').read_bytes()==b'p2-fixedvolt-1200mhz\0'
assert Path('/sys/module/cpufreq/parameters/off').read_text().strip()=='0'
assert Path('/sys/module/cpufreq/parameters/default_governor').read_text().strip()=='powersave'
assert not list(Path('/sys/devices/system/cpu/cpufreq').glob('policy*'))
p=Path('/usr/local/lib/f8-pro/experimental/f8-cpufreq-p2.ko')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='f68a2ee60888b8bd1ece356bf546d3729d234c9d7297095139713afd11706f27'
r=subprocess.run(['insmod',str(p)],capture_output=True,text=True,timeout=15);time.sleep(1)
out={'load_exit':r.returncode,'stderr':r.stderr,'policies':{},'cooling':[]}
for p in Path('/sys/devices/system/cpu/cpufreq').glob('policy*'):
 out['policies'][p.name]={x:(p/x).read_text().strip() for x in ['scaling_driver','scaling_governor','scaling_available_frequencies','related_cpus','scaling_cur_freq','scaling_min_freq','scaling_max_freq']}
for p in Path('/sys/class/thermal').glob('cooling_device*'):
 out['cooling'].append({'type':(p/'type').read_text().strip(),'max_state':(p/'max_state').read_text().strip()})
out['kernel_tail']=subprocess.run(['journalctl','-k','-b','-n','45','--no-pager'],capture_output=True,text=True,timeout=10).stdout
print(json.dumps(out,indent=2))
