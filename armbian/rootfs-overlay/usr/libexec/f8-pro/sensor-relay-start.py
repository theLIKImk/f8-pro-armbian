#!/usr/bin/python3
import os,json,hashlib,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.uname().release=='6.1.115-vendor-rk35xx'
p=Path('/usr/lib/modules')/os.uname().release/'extra/f8-pro/f8_sensor_relay.ko'
m=json.loads(Path('/usr/share/f8-pro/sensor-relay-r1/module-check.json').read_text())
assert hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256']
assert m['all_import_crcs_verified_against_actual_image']
subprocess.run(['modprobe','f8_sensor_relay'],check=True)
