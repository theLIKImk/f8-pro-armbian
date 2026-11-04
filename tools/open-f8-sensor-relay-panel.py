import json,subprocess,pwd,os
from pathlib import Path
pre=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
envout=subprocess.check_output(pre+['systemctl','--user','show-environment'],text=True);session={}
for line in envout.splitlines():
 if '=' in line:
  k,v=line.split('=',1)
  if k in ['DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','LANG']:session[k]=v
cmd=pre+['systemd-run','--user','--collect','--unit=f8-sensor-relay-panel-live','--setenv=QT_QPA_PLATFORM=wayland']+['--setenv='+k+'='+v for k,v in session.items()]+['/usr/local/bin/f8-sensor-relay']
r=subprocess.run(cmd,capture_output=True,text=True,timeout=10)
print(json.dumps({'panel_exit':r.returncode,'panel_message':r.stderr,'snapshot':json.loads(Path('/run/user/1602/f8-sensor-relay.json').read_text())}))
