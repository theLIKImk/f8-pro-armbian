#!/usr/bin/python3
"""Late bind only the F8's confirmed EM30918; do not scan or force I2C addresses."""
import fcntl,hashlib,json,os,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.uname().release=='6.1.115-vendor-rk35xx'
assert Path('/sys/bus/i2c/devices/3-0068/name').read_text().strip()=='mpu6500'
module=Path('/usr/lib/modules')/os.uname().release/'extra/f8-pro/f8_em30918.ko'
manifest=json.loads(Path('/usr/share/f8-pro/sensors-f2/em30918-module.json').read_text())
assert hashlib.sha256(module.read_bytes()).hexdigest()==manifest['sha256']
with open('/run/lock/f8-optical.lock','w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 client=Path('/sys/bus/i2c/devices/3-0024')
 if client.exists():assert (client/'driver').resolve().name=='f8-em30918','Address already owned by another driver'
 else:
  subprocess.run(['modprobe','f8_em30918'],check=True)
  Path('/sys/bus/i2c/devices/i2c-3/new_device').write_text('f8-em30918 0x24\n')
  for _ in range(20):
   if (client/'driver').exists():break
   time.sleep(.05)
  if not (client/'driver').exists():
   Path('/sys/bus/i2c/devices/i2c-3/delete_device').write_text('0x24\n');raise RuntimeError('EM30918 ID/probe check failed')
 assert (client/'driver').resolve().name=='f8-em30918'
 print('F8 EM30918 raw ambient/proximity ready; ALS/proximity units uncalibrated')
