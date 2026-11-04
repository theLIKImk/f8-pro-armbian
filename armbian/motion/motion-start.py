#!/usr/bin/python3
"""Load verified IIO modules only under the S1 board profile."""
import hashlib,json,subprocess,time
from pathlib import Path
dt=Path('/sys/firmware/devicetree/base')
assert (dt/'chosen/f8-motion-trial').read_bytes()==b's1\0'
assert (dt/'i2c@feab0000/imu@68/compatible').read_bytes()==b'invensense,mpu6500\0'
assert (dt/'i2c@feab0000/mpu_acc@68/status').read_bytes()==b'disabled\0'
assert not Path('/sys/bus/i2c/devices/3-0068/driver').exists(),'Unexpected pre-existing sensor driver'
modules=[('inv-mpu6050.ko','9ef1b1114ec4a9deca6d5ec65ce6bf0c020cfb5bfb528c8c54cb19d0d4f9b3e0'),
 ('inv-mpu6050-i2c.ko','ef3f5c77773790b52b2e883dfbe1e37137a09d7c44f183a31fca2e2d307b93c1')]
for name,digest in modules:
    p=Path('/usr/libexec/f8-pro/motion')/name
    assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,name
for name,digest in modules:
    subprocess.run(['insmod','/usr/libexec/f8-pro/motion/'+name],check=True,timeout=10)
deadline=time.monotonic()+5
while True:
    devices=[p for p in Path('/sys/bus/iio/devices').glob('iio:device*') if (p/'name').read_text().strip()=='mpu6500']
    if devices:break
    assert time.monotonic()<deadline,'MPU6500 did not bind; inspect dmesg, do not scan/reset other devices'
    time.sleep(.2)
assert len(devices)==1
for kind in ['accel','anglvel']:
    for axis in 'xyz':assert (devices[0]/f'in_{kind}_{axis}_raw').is_file()
subprocess.run(['udevadm','settle','--timeout=5'],check=True,timeout=7)
subprocess.run(['systemctl','start','--no-block','iio-sensor-proxy.service'],check=True,timeout=5)
print(json.dumps({'iio_device':str(devices[0]),'combined_accel_gyro':True,'polling':True,'physical_motion_verified':False}))
