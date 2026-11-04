#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
def read(p):
    try:return p.read_text()[-14000:]
    except OSError as e:return {'error':str(e)}
roots=[Path('/sys/kernel/debug/usb'),Path('/sys/kernel/debug/typec'),Path('/sys/kernel/debug/fusb302')]
files={}
for root in roots:
    if root.exists():
        for p in root.rglob('*'):
            if p.is_file() and p.name in ['mode','log','tcpm_log']:
                files[str(p)]=read(p)
regulators={p.name:{n:read(p/n) for n in ['name','state','status','num_users','microvolts'] if (p/n).exists()} for p in Path('/sys/class/regulator').glob('*') if (p/'name').exists() and 'f8_usb' in (p/'name').read_text()}
gpio=Path('/sys/kernel/debug/gpio')
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'usb_debug_files':files,'regulators':regulators,'otg_gpio_lines':[s for s in gpio.read_text().splitlines() if 'gpio-134 ' in s],'usb_debug_paths':[str(p) for root in roots if root.exists() for p in root.rglob('*')][:100]},indent=2))
PY
