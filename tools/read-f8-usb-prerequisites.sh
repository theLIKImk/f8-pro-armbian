#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,re,subprocess
from pathlib import Path
def read(p):
    try:return p.read_text().strip()
    except OSError:return None
pins={str(p):[s for s in p.read_text().splitlines() if re.search(r'^pin (20|134) \(',s)] for p in Path('/sys/kernel/debug/pinctrl').glob('*/pinmux-pins')}
gpio=Path('/sys/kernel/debug/gpio')
print(json.dumps({'boot_id':read(Path('/proc/sys/kernel/random/boot_id')),'pinmux':pins,'gpio':read(gpio),
 'i2c6_devices':{p.name:{'driver':str((p/'driver').resolve()) if (p/'driver').is_symlink() else None,'name':read(p/'name')} for p in Path('/sys/bus/i2c/devices').glob('6-*')},
 'headers_link':str(Path('/lib/modules/6.1.115-vendor-rk35xx/build').resolve()),
 'config_exists':Path('/proc/config.gz').exists(),'regulators':{p.name:read(p/'name') for p in Path('/sys/class/regulator').glob('*')},
 'scope':'Read-only GPIO ownership and driver prerequisites; no bus scan or register writes'},indent=2))
PY
