#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,hashlib,subprocess
from pathlib import Path
out={}
for name in ['/etc/udev/rules.d/70-f8-cover-haptic.rules','/home/f8test/.config/plasmakeyboardrc','/usr/share/dbus-1/services/org.sigxcpu.Feedback.service']:
    p=Path(name);out[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'text':p.read_text()}
out['motor_active']=Path('/sys/devices/platform/f8-cover-haptic/motor_active').read_text().strip()
out['boot_id']=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
out['tainted']=Path('/proc/sys/kernel/tainted').read_text().strip()
out['kernel_oops_found']=any(x in subprocess.check_output(['dmesg'],text=True) for x in ['Oops:','Internal error:','Kernel panic'])
out['failed']=subprocess.check_output(['systemctl','--failed','--no-pager'],text=True)
out['packages']=subprocess.check_output(['dpkg-query','-W','feedbackd','feedbackd-common','plasma-keyboard'],text=True)
out['processes']=subprocess.check_output(['pgrep','-af','/usr/libexec/feedbackd|/usr/bin/plasma-keyboard'],text=True)
print(json.dumps(out,indent=2))
PY
