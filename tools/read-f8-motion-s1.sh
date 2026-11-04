#!/bin/sh
# Bounded readout of IIO axes; no raw I2C access or orientation changes.
set -eu
python3 -I - <<'PY'
import json,subprocess,time
from pathlib import Path
def run(args):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=10)
        return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except Exception as e:return {'error':str(e)}
dt=Path('/sys/firmware/devicetree/base');assert (dt/'chosen/f8-motion-trial').read_bytes()==b's1\0'
devices=[p for p in Path('/sys/bus/iio/devices').glob('iio:device*') if (p/'name').read_text().strip()=='mpu6500']
results=[]
for p in devices:
    meta={f.name:f.read_text().strip() for f in p.iterdir() if f.is_file() and any(s in f.name for s in ['scale','mount_matrix','sampling_frequency'])}
    samples=[]
    for _ in range(12):
        sample={'monotonic':time.monotonic()}
        for kind in ['accel','anglvel']:
            for axis in 'xyz':
                name=f'in_{kind}_{axis}_raw'
                try:sample[name]=int((p/name).read_text())
                except OSError as e:sample[name]={'error':str(e)}
        samples.append(sample);time.sleep(.1)
    results.append({'device':str(p),'meta':meta,'samples':samples})
sockets=[p.name for p in Path('/run/user/1601').glob('wayland-*') if p.is_socket()]
user=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus','QT_QPA_PLATFORM=wayland','WAYLAND_DISPLAY='+(sockets[0] if sockets else 'wayland-0')]
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'devices':results,
 'services':run(['systemctl','status','f8-motion','iio-sensor-proxy','--no-pager','-l']),
 'has_accelerometer':run(['busctl','get-property','net.hadess.SensorProxy','/net/hadess/SensorProxy','net.hadess.SensorProxy','HasAccelerometer']),
 'orientation':run(['busctl','get-property','net.hadess.SensorProxy','/net/hadess/SensorProxy','net.hadess.SensorProxy','AccelerometerOrientation']),
 'display':run(user+['kscreen-doctor','-j']),
 'kernel_logs':run(['sh','-c',"dmesg | grep -Ei 'mpu|feab0000|inv_mpu|dummy regulator' | tail -40"]),
 'failed':run(['systemctl','--failed','--no-legend','--no-pager']),
 'other_services':run(['systemctl','is-active','sddm','f8-usb-otg','f8-bluetooth'])},indent=2))
PY
