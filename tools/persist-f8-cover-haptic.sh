#!/bin/sh
set -eu
python3 -I - <<'PY'
import hashlib,json,subprocess
from pathlib import Path
p=Path('/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8-cover-haptic.ko');assert hashlib.sha256(p.read_bytes()).hexdigest()=='a33e43d75e77ca997527608b2f97ab1971ae04bf7127be3d123e7172a05fcc4c'
assert Path('/sys/devices/platform/f8-cover-haptic/motor_active').read_text().strip()=='0'
config=Path('/etc/modules-load.d/f8-cover-haptic.conf');assert not config.exists();config.write_text('f8-cover-haptic\n');config.chmod(0o644)
log=subprocess.check_output(['dmesg'],text=True)
print(json.dumps({'module_autoload':str(config),'boot_tested':False,'kernel_oops_found':any(x in log for x in ['Oops:','Internal error:','Kernel panic']),'tainted':Path('/proc/sys/kernel/tainted').read_text().strip(),'failed':subprocess.check_output(['systemctl','--failed','--no-pager'],text=True)},indent=2))
PY
