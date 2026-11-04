"""Reboot the unplugged tablet after checking the installed USB startup service."""
import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];dest=P/'local/hardware/armbian-native-usb-20261101/u5'
out=dest/'reboot-request01.json';runner=dest/'reboot-request01-runner.sh';assert not out.exists() and not runner.exists()
runner.write_text('''#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='9df01d2b-d624-4364-8d3d-a06ff6847720'
assert not Path('/sys/class/typec/port0-partner').exists(),'Tablet USB port must be empty'
reg=next(p for p in Path('/sys/class/regulator').glob('*') if (p/'name').exists() and (p/'name').read_text().strip()=='f8_usb_otg_vbus')
assert (reg/'state').read_text().strip()=='disabled'
assert not any(s.split()[0].startswith('/dev/sda') for s in Path('/proc/mounts').read_text().splitlines())
assert subprocess.check_output(['systemctl','is-enabled','f8-usb-otg.service'],text=True).strip()=='enabled'
assert subprocess.check_output(['systemctl','is-active','f8-usb-otg.service'],text=True).strip()=='active'
subprocess.run(['journalctl','--sync'],check=True,timeout=15)
subprocess.run(['sync'],check=True,timeout=15)
r=subprocess.run(['systemd-run','--unit=f8-usb-u5-reboot','--on-active=3s','/usr/bin/systemctl','reboot'],capture_output=True,text=True,timeout=10)
assert r.returncode==0,r.stderr
print(json.dumps({'previous_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'usb_port_empty':True,'vbus_disabled':True,'usb_filesystems_unmounted':True,'reboot_scheduled':True,'delay_seconds':3}))
PY
''')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1600:]
d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
