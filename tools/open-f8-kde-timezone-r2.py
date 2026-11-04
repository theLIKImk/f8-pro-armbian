import subprocess,json
from pathlib import Path
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
env=run(u+['systemctl','--user','show-environment'])['stdout'];session={k:v for line in env.splitlines() if '=' in line for k,v in [line.split('=',1)] if k in ['DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','LANG']}
args=[f'{k}={v}' for k,v in session.items()]
log='/run/user/1602/f8-timezone-page-r2.log'
o={'launch':run(u+['systemd-run','--user','--collect','--unit=f8-timezone-kcm-r2','--property=StandardOutput=append:'+log,'--property=StandardError=append:'+log,'/usr/bin/env',*args,'QT_QPA_PLATFORM=wayland','/usr/bin/kcmshell6','kcm_clock']),'map_install':run(['journalctl','-u','f8-kde-timezone-map-deps.service','-n','12','--no-pager']),'plugins':run(['dpkg','-L','qt6-location-plugins']),'map_owner':run(['dpkg-query','-S','/usr/share/timezonefiles/timezones.json'])}
import time;time.sleep(2)
p=Path(log);o['page_log']=p.read_text(errors='replace') if p.exists() else ''
o['active']=run(u+['systemctl','--user','is-active','f8-timezone-kcm-r2.service'])
print(json.dumps(o))
