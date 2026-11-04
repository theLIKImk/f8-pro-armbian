#!/usr/bin/python3
"""Bind the official AK8963 IIO driver to the board's verified address."""
import hashlib,json,subprocess,time
from pathlib import Path
dt=Path('/sys/firmware/devicetree/base')
assert (dt/'chosen/f8-motion-trial').read_bytes()==b's1\0'
assert (dt/'i2c@feab0000/ak8963@f/status').read_bytes()==b'disabled\0'
assert Path('/sys/bus/i2c/devices/3-0068/driver').resolve().name=='inv-mpu6050-i2c'
module=Path('/usr/libexec/f8-pro/compass/ak8975_magn.ko')
assert hashlib.sha256(module.read_bytes()).hexdigest()=='b97278dbecb43085d54c9e811a4af1105caf556fb9d722585a21671d79b22d31'
client=Path('/sys/bus/i2c/devices/3-000f')
if not client.exists():
    identity=subprocess.check_output(['i2ctransfer','-y','3','w1@0x0f','0x00','r2'],text=True,timeout=8).split()
    assert identity[0]=='0x48',identity
if not Path('/sys/module/ak8975_magn').exists():subprocess.run(['insmod',str(module)],check=True,timeout=10)
if not client.exists():
    # The official driver has an uppercase ID; the vendor input driver does not.
    # Avoid loading/binding the competing legacy lowercase ak8963 client.
    Path('/sys/bus/i2c/devices/i2c-3/new_device').write_text('AK8963 0x0f\n')
deadline=time.monotonic()+4
while not (client/'driver').exists():
    assert time.monotonic()<deadline,'AK8963 probe failed; inspect kernel log'
    time.sleep(.2)
assert (client/'driver').resolve().name=='ak8975_magn'
print(json.dumps({'address':'3-000f','driver':'ak8975_magn','name':(client/'name').read_text().strip(),'calibrated':False}))
