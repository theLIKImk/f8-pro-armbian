#!/bin/sh
set -eu
python3 -I - <<'PY'
import json
from pathlib import Path
def read(p):
    try:return p.read_text()[-10000:]
    except OSError as e:return {'error':str(e)}
phy=Path('/sys/bus/platform/devices/fd5d0000.syscon:usb2-phy@0')
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'phy_files':[p.name for p in phy.iterdir()],
 'phy_instances':{p.name:str(p.resolve()) for p in Path('/sys/class/phy').glob('*')},
 'typec_mux_devices':[p.name for p in Path('/sys/class/typec_mux').glob('*')],
 'phy_otg_mode':read(phy/'otg_mode'),'dwc3_mode':read(Path('/sys/kernel/debug/usb/fc000000.usb/mode')),
 'typec':{p.name:{n:read(p/n) for n in ['data_role','power_role','orientation'] if (p/n).exists()} for p in Path('/sys/class/typec').glob('*')},
 'regulators':{p.name:{n:read(p/n) for n in ['name','state','num_users'] if (p/n).exists()} for p in Path('/sys/class/regulator').glob('*') if (p/'name').exists() and 'f8_usb' in (p/'name').read_text()},
 'extcon':{p.name:{n:read(p/n) for n in ['name','state'] if (p/n).exists()} for p in Path('/sys/class/extcon').glob('*')}},indent=2))
PY
