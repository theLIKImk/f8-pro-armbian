#!/bin/sh
set -eu
python3 -I - <<'PY'
import hashlib,json,subprocess
from pathlib import Path
names=['/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8-cover-haptic.ko','/etc/udev/rules.d/70-f8-cover-haptic.rules','/etc/modules-load.d/f8-cover-haptic.conf','/usr/local/bin/f8-vibrate','/usr/local/lib/f8-pro/cover-screen.py','/usr/local/lib/f8-pro/cover-haptic-test.py','/usr/local/bin/f8-cover-test','/usr/share/applications/f8-cover-test.desktop','/home/f8test/.config/systemd/user/f8-cover-screen.service','/home/f8test/.config/f8-cover.json']
files={n:{'sha256':hashlib.sha256(Path(n).read_bytes()).hexdigest(),'bytes':Path(n).stat().st_size,'mode':oct(Path(n).stat().st_mode&0o7777)} for n in names}
log=subprocess.check_output(['dmesg'],text=True)
pins='\n'.join(p.read_text() for p in Path('/sys/kernel/debug/pinctrl').glob('*/pinmux-pins'))
out={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'files':files,'observer':json.loads(Path('/home/f8test/.cache/f8-cover/status.json').read_text()),'hall_raw':Path('/sys/devices/platform/f8-cover-haptic/hall_raw').read_text().strip(),'motor_active':Path('/sys/devices/platform/f8-cover-haptic/motor_active').read_text().strip(),'pins':[s for s in pins.splitlines() if any(s.startswith('pin '+str(n)+' ') for n in [27,114,138])],'gpio':Path('/sys/kernel/debug/gpio').read_text(),'input':Path('/proc/bus/input/devices').read_text(),'kernel_oops_found':any(s in log for s in ['Oops:','Internal error:','Kernel panic']),'tainted':Path('/proc/sys/kernel/tainted').read_text().strip(),'failed':subprocess.check_output(['systemctl','--failed','--no-pager'],text=True)}
print(json.dumps(out,indent=2))
PY
