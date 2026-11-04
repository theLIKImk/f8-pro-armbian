import json,subprocess,os,time,errno
from pathlib import Path
def run(a):
 p=subprocess.run(a,capture_output=True,text=True,timeout=10);return {'exit':p.returncode,'out':p.stdout[-9000:],'err':p.stderr[-1000:]}
pre=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
o={'panel_log':run(['journalctl','_UID=1602','_SYSTEMD_USER_UNIT=f8-sensor-relay-panel-live.service','-n','20','--no-pager']),'idle':run(pre+['gdbus','call','--session','--dest','org.freedesktop.ScreenSaver','--object-path','/ScreenSaver','--method','org.freedesktop.ScreenSaver.GetSessionIdleTime'])}
p=next(p for p in Path('/sys/bus/iio/devices').glob('iio:device*') if (p/'name').read_text().strip()=='f8-sensor-relay')
run(pre+['systemctl','--user','stop','f8-sensor-relay.service']);time.sleep(.8)
try:
 fd=os.open(p/'in_accel_x_raw',os.O_RDONLY)
 try:
  try:o['stale_read']=repr(os.read(fd,100))
  except OSError as e:o['stale_exception']={'errno':e.errno,'message':str(e)}
 finally:os.close(fd)
finally:run(pre+['systemctl','--user','start','f8-sensor-relay.service'])
# Offscreen smoke render as real desktop account, terminate after 3s.
try:
 r=subprocess.run(pre+['QT_QPA_PLATFORM=offscreen','/usr/bin/python3','/usr/local/lib/f8-pro/sensor-relay-panel.py'],capture_output=True,text=True,timeout=3);o['panel_smoke']={'exit':r.returncode,'stderr':r.stderr}
except subprocess.TimeoutExpired as e:o['panel_smoke']={'running_after_3s':True,'stderr':(e.stderr or b'').decode(errors='replace') if isinstance(e.stderr,bytes) else e.stderr}
print(json.dumps(o))
