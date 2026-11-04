import json,subprocess,base64,hashlib
from pathlib import Path
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=12);assert r.returncode==0,r.stderr;return r.stdout
env=run(u+['systemctl','--user','show-environment']);session={k:v for line in env.splitlines() if '=' in line for k,v in [line.split('=',1)] if k in ['DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','LANG']}
args=[f'{k}={v}' for k,v in session.items()]
run(u+['systemd-run','--user','--collect','--unit=f8-sensors-f2-final-live','/usr/bin/env',*args,'QT_QPA_PLATFORM=wayland','/usr/bin/python3','/usr/local/lib/f8-pro/sensor-monitor.py'])
sample=json.loads(Path('/run/user/1602/f8-sensors-f2-final.json').read_text())
c=json.loads(Path('/home/likimk/.config/f8-pro/compass-calibration.json').read_text())
print(json.dumps({'sample':sample,'calibration_version':c['version'],'calibration_3d_radius_ut':c.get('field_radius_ut'),'image_b64':base64.b64encode(Path('/run/user/1602/f8-sensors-f2-final.png').read_bytes()).decode(),'optical_service':run(['systemctl','is-active','f8-optical.service']),'module_hash':hashlib.sha256(Path('/usr/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8_em30918.ko').read_bytes()).hexdigest(),'kernel_errors':run(['journalctl','-k','--since=-10min','--no-pager','-p','err'])}))
