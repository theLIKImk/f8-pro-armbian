import subprocess,json,time,os,errno
from pathlib import Path
pre=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);return {'exit':r.returncode,'out':r.stdout[:5000],'err':r.stderr[:700]}
o={'screensaver':run(pre+['busctl','--user','introspect','org.freedesktop.ScreenSaver','/ScreenSaver']),'dbus_settings':run(pre+['gdbus','call','--session','--dest','net.f8.Sensors','--object-path','/net/f8/Sensors','--method','net.f8.Sensors1.GetSettings']),'orientation_proxy':run(['busctl','--system','get-property','net.hadess.SensorProxy','/net/hadess/SensorProxy','net.hadess.SensorProxy','HasAccelerometer']),'module':run(['lsmod']),'panel':run(pre+['systemctl','--user','is-active','f8-sensor-relay-panel-live.service'])}
# Stale data must stop being readable through native IIO when feeder stops.
p=next(p for p in Path('/sys/bus/iio/devices').glob('iio:device*') if (p/'name').read_text().strip()=='f8-sensor-relay')
run(pre+['systemctl','--user','stop','f8-sensor-relay.service']);time.sleep(.8)
try:
 try:(p/'in_accel_x_raw').read_text();o['stale_rejected']=False
 except OSError as e:o['stale_rejected']=e.errno==errno.EAGAIN;o['stale_errno']=e.errno
finally:run(pre+['systemctl','--user','start','f8-sensor-relay.service'])
time.sleep(2);o['snapshot']=json.loads(Path('/run/user/1602/f8-sensor-relay.json').read_text())
print(json.dumps(o))
