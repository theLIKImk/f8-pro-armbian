#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,time,subprocess
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='d83ba29d-2d56-4a09-8240-2bee4bf10466'
status=Path('/sys/bus/i2c/devices/6-006a/f8_usb_status/status')
def read(p):
    try:return p.read_text().strip()
    except OSError as e:return {'error':str(e)}
samples=[]
for i in range(6):
    raw=read(status);values={key:int(value,16) for key,value in (s.split('=') for s in raw.split())}
    samples.append({'monotonic':time.monotonic(),'raw':values,'vbus_status_code':(values['reg0b']>>5)&7,'otg_bit':bool(values['reg03']&32),
                    'typec_data_role':read(Path('/sys/class/typec/port0/data_role')),'typec_power_role':read(Path('/sys/class/typec/port0/power_role')),
                    'dwc3_mode':read(Path('/sys/kernel/debug/usb/fc000000.usb/mode'))})
    if i<5:time.sleep(1)
devices={p.name:{n:read(p/n) for n in ['idVendor','idProduct','product','speed'] if (p/n).exists()} for p in Path('/sys/bus/usb/devices').glob('*') if (p/'idVendor').exists()}
reg=next(p for p in Path('/sys/class/regulator').glob('*') if (p/'name').exists() and (p/'name').read_text().strip()=='f8_usb_otg_vbus')
debug={str(p):read(p) for p in [Path('/sys/kernel/debug/usb/tcpm-6-0022/log'),Path('/sys/kernel/debug/usb/fusb302-6-0022/log')] if p.exists()}
for key in debug:
    if isinstance(debug[key],str):debug[key]=debug[key][-18000:]
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'samples':samples,'usb_devices':devices,
 'regulator':{n:read(reg/n) for n in ['name','state','num_users','microvolts'] if (reg/n).exists()},
 'gpio_lines':[s for s in Path('/sys/kernel/debug/gpio').read_text().splitlines() if 'gpio-134 ' in s],
 'debug':debug,'note':'Passive driver reads only; REG11 is cached ADC, not fresh voltage; no register writes/ADC/fault-latch reads'},indent=2))
PY
