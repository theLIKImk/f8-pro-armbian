#!/bin/sh
# Fixed-address chip identity reads only; never force access to a bound client.
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
def run(args):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=10)
        return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except Exception as e:return {'error':str(e)}
assert Path('/sys/firmware/devicetree/base/chosen/f8-motion-trial').read_bytes()==b's1\0'
assert not Path('/sys/bus/i2c/devices/3-000f/driver').exists()
results={
 'identity_0f':run(['i2ctransfer','-y','3','w1@0x0f','0x00','r2']),
 'driver':run(['modinfo','ak8975']),
 'config':run(['sh','-c',"grep -E '^CONFIG_(AK8975|COMPASS_AK8963|I2C_CHARDEV)' /boot/config-$(uname -r)"]),
 'clients':run(['sh','-c','ls -l /sys/bus/i2c/devices/3-*']),
 'services':run(['systemctl','is-active','f8-motion','iio-sensor-proxy','f8-bluetooth','f8-usb-otg','sddm'])}
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'results':results},indent=2))
PY
