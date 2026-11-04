#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
def run(args):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=12)
        return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except Exception as e:return {'error':str(e)}
dt=Path('/sys/firmware/devicetree/base');nodes={}
for p in dt.rglob('compatible'):
    if any(x in p.read_bytes().lower() for x in [b'mpu',b'ak896',b'feab0000'] ) or p.parent.name=='i2c@feab0000':
        nodes[str(p.parent.relative_to(dt))]={q.name:q.read_bytes().hex() for q in p.parent.iterdir() if q.is_file()}
commands={
 'config':['sh','-c',"grep -E 'CONFIG_(INV_MPU|IIO|MPU6500|GYRO|GSENSOR|SENSOR|COMPASS|AK897)' /boot/config-$(uname -r)"],
 'modules':['sh','-c',"find /lib/modules/$(uname -r) -iname '*mpu*' -o -iname '*ak89*'; lsmod | grep -E 'sensor|mpu|iio|gyro'"],
 'i2c':['sh','-c',"ls -l /sys/bus/i2c/devices/3-*; cat /sys/bus/i2c/devices/i2c-3/name"],
 'iio':['sh','-c',"for d in /sys/bus/iio/devices/iio:device*; do echo $d; cat $d/name; ls $d; done"],
 'input':['cat','/proc/bus/input/devices'],
 'logs':['sh','-c',"dmesg | grep -Ei 'mpu|ak896|gsensor|gyros|feab0000|i2c3'"],
 'packages':['sh','-c',"dpkg-query -W iio-sensor-proxy libiio-utils 2>/dev/null; command -v monitor-sensor; systemctl status iio-sensor-proxy --no-pager -l"],
 'pinmux':['sh','-c',"grep -E 'feab0000|pin (49|50|59) ' /sys/kernel/debug/pinctrl/*/pinmux-pins"],
 'power':['cat','/sys/kernel/debug/regulator/regulator_summary']}
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'nodes':nodes,'checks':{k:run(v) for k,v in commands.items()}},indent=2))
PY
