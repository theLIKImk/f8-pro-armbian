import json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
def read(p):
 try:return Path(p).read_text().strip().strip('\0')
 except OSError:return None
out={'boot_id':read('/proc/sys/kernel/random/boot_id'),'cpu_trial':read('/proc/device-tree/chosen/f8-cpu-trial'),'gpu_trial':read('/proc/device-tree/chosen/f8-gpu-trial'),'cmdline':read('/proc/cmdline'),'core_off':read('/sys/module/cpufreq/parameters/off'),'default_governor':read('/sys/module/cpufreq/parameters/default_governor'),'module_loaded':Path('/sys/module/f8_cpufreq_p2').exists(),'policies':[str(p) for p in Path('/sys/devices/system/cpu/cpufreq').glob('policy*')]}
clk=read('/sys/kernel/debug/clk/clk_summary') or '';out['cpu_clocks']=[s for s in clk.splitlines() if 'scmi_clk_cpu' in s]
out['regulators']=[]
for p in Path('/sys/class/regulator').glob('*'):
 n=read(p/'name')
 if n and n.startswith('vdd_cpu'):out['regulators'].append({'name':n,'uv':read(p/'microvolts')})
out['temps']=[{'name':read(p/'type'),'temp':read(p/'temp')} for p in Path('/sys/class/thermal').glob('thermal_zone*')]
print(json.dumps(out,indent=2))
