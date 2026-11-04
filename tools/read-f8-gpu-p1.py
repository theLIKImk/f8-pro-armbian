"""Read-only post-boot GPU trial verification. Does not set clocks or voltages."""
import json,os,subprocess
from pathlib import Path
assert os.geteuid()==0
def read(p):
 try:return Path(p).read_text().strip()
 except OSError:return None
out={'kernel':subprocess.check_output(['uname','-r'],text=True).strip(),'cmdline':read('/proc/cmdline'),'boot_id':read('/proc/sys/kernel/random/boot_id'),'trial':read('/proc/device-tree/chosen/f8-gpu-trial'),'devfreq':{},'thermal':[],'regulators':[]}
for p in Path('/sys/class/devfreq').glob('*gpu*'):
 out['devfreq'][p.name]={x:read(p/x) for x in ['governor','available_frequencies','cur_freq','min_freq','max_freq','trans_stat']}
for p in Path('/sys/class/thermal').glob('*'):
 typ=read(p/'type')
 if typ and ('gpu' in typ or p.name.startswith('cooling_device')):
  out['thermal'].append({'path':str(p),'type':typ,'temp':read(p/'temp'),'cur_state':read(p/'cur_state'),'max_state':read(p/'max_state'),'trips':{x.name:read(x) for x in p.glob('trip_point_*')},'cooling_links':{x.name:str(x.resolve()) for x in p.glob('cdev*') if x.is_symlink()}})
for p in Path('/sys/class/regulator').glob('*'):
 if read(p/'name')=='vdd_gpu_s0':out['regulators'].append({'name':'vdd_gpu_s0','uv':read(p/'microvolts')})
clk=read('/sys/kernel/debug/clk/clk_summary') or ''
out['cpu_clocks']=[x for x in clk.splitlines() if 'scmi_clk_cpu' in x]
out['gpu_clocks']=[x for x in clk.splitlines() if any(s in x for s in ['scmi_clk_gpu','clk_gpu'])]
log=subprocess.run(['journalctl','-k','-b','--no-pager'],capture_output=True,text=True,timeout=15).stdout
out['gpu_kernel_lines']=[x for x in log.splitlines() if any(s in x.lower() for s in ['panthor','cooling device','gpu fault','gpu hang','oops:'])][-60:]
print(json.dumps(out,indent=2))
