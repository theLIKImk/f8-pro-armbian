#!/bin/sh
# Original BOOT control measurement through its native power_supply driver only.
set -eu
test -f /etc/arch-release
case "$(uname -r)" in 5.10.160*) ;; *) echo 'Wrong kernel for original control' >&2; exit 1;; esac
python3 -I - <<'PY'
import json,time,os
from pathlib import Path
samples=[]
names=['type','status','online','health','present','capacity','voltage_now','voltage_avg','voltage_max',
 'current_now','current_avg','current_max','constant_charge_voltage','constant_charge_voltage_max',
 'constant_charge_current','constant_charge_current_max','input_current_limit','input_voltage_limit',
 'charge_term_current','temp','charge_type']
for index in range(5):
    row={'uptime':float(Path('/proc/uptime').read_text().split()[0]),'supplies':{}}
    for supply in Path('/sys/class/power_supply').iterdir():
        values={}
        for name in names:
            path=supply/name
            if path.is_file():
                try:values[name]=path.read_text().strip()
                except OSError as error:values[name]={'error':str(error)}
        row['supplies'][supply.name]=values
    samples.append(row)
    if index<4:time.sleep(5)
print(json.dumps({'scope':'Original BOOT native charger API control, no raw I2C or sysfs writes',
 'kernel':os.uname().release,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'samples':samples},indent=2))
PY
