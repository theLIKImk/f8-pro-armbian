"""Read-only full-performance cold-boot verification; does not apply a profile."""
import json,os,re,subprocess,sys
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
sys.path.insert(0,'/usr/local/lib/f8-pro');from performance_state import snapshot,profile
out={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'uptime_seconds':float(Path('/proc/uptime').read_text().split()[0]),'profile':profile(),'devices':{k:snapshot(k) for k in ['gpu','cpu0','cpu4','cpu6']},'services':{}}
for name in ['f8-performance-gpu-start.service','f8-performance-cpu-start.service']:
 r=subprocess.run(['systemctl','show',name,'-p','ActiveState','-p','SubState','-p','Result','-p','ExecMainStatus'],capture_output=True,text=True,timeout=8)
 out['services'][name]=r.stdout
out['module_loaded']=Path('/sys/module/f8_cpufreq_p3').exists()
out['failed_units']=subprocess.run(['systemctl','--failed','--no-legend','--no-pager'],capture_output=True,text=True,timeout=8).stdout
log=subprocess.run(['journalctl','-k','-b','--no-pager'],capture_output=True,text=True,timeout=10).stdout
out['faults']=[s for s in log.splitlines() if re.search(r'\bOops:|\bBUG:|gpu.*(fault|hang|timeout)|panthor.*(error|reset)',s,re.I)]
out['calibration_lines']=[s for s in log.splitlines() if 'f8-cpufreq-p3: cpu' in s or 'pvtm-volt-sel=' in s]
print(json.dumps(out,indent=2))
