#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='532eb6df-13ce-4e63-9645-24d4136d96b9'
for name in ['rkisp0-vir0','rkisp1-vir0','rkcif-mipi-lvds2-sditf','rkcif-mipi-lvds3-sditf']:
    assert (Path('/sys/bus/platform/devices')/name/'driver').exists(),name
# All devices are bound: no live media reprobe can occur. This tests only
# idempotent modprobe + sensor control persistence, without restarting a unit.
p=subprocess.run(['python3','/usr/libexec/f8-pro/camera-start.py'],capture_output=True,text=True,timeout=15)
assert p.returncode==0,(p.stdout,p.stderr)
result=json.loads(p.stdout)
assert all(v['already_bound'] for v in result['late_initial_probes'].values())
assert all('error' not in v for v in result['c4_online_blanking'].values())
health=subprocess.run(['systemctl','--failed','--no-pager'],capture_output=True,text=True)
log=subprocess.check_output(['dmesg'],text=True)
print(json.dumps({'runtime_check':result,'failed_units':health.stdout,'tainted':Path('/proc/sys/kernel/tainted').read_text().strip(),
 'kernel_oops_found':any(s in log for s in ['Internal error:','Kernel panic','Oops:']),
 'aiq_server_process':subprocess.run(['pgrep','-x','rkaiq_3A_server'],capture_output=True,text=True).stdout,
 'no_capture_started':True,'service_restarted':False},indent=2))
PY
