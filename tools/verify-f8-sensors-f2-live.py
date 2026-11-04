import json,subprocess,time,math
from pathlib import Path
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
def run(a,check=True):
 r=subprocess.run(a,capture_output=True,text=True,timeout=12)
 if check:assert r.returncode==0,r.stderr
 return r
c=json.loads(Path('/home/likimk/.config/f8-pro/compass-calibration.json').read_text());assert c['version']==2 and c.get('field_radius_ut'),{k:c.get(k) for k in ['version','method']}
if run(u+['systemctl','--user','is-active','f8-sensors-f2-final-live.service'],False).returncode==0:run(u+['systemctl','--user','restart','f8-sensors-f2-final-live.service'])
else:
 env=run(u+['systemctl','--user','show-environment']).stdout;session={k:v for line in env.splitlines() if '=' in line for k,v in [line.split('=',1)] if k in ['DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','LANG']};args=[f'{k}={v}' for k,v in session.items()]
 run(u+['systemd-run','--user','--collect','--unit=f8-sensors-f2-verified-live','/usr/bin/env',*args,'QT_QPA_PLATFORM=wayland','python3','/usr/local/lib/f8-pro/sensor-monitor.py'])
time.sleep(3)
s=json.loads(Path('/run/user/1602/f8-sensor-fusion.json').read_text())
assert s['valid'] and s['online'] and s['absolute_valid'],s
for key in ['game_rotation_vector_wxyz','rotation_vector_wxyz','geomagnetic_rotation_vector_wxyz']:assert abs(sum(v*v for v in s[key])-1)<1e-6
print(json.dumps({'calibration_version':c['version'],'calibration_samples':c['sample_count'],'sphere_radius_ut':c['field_radius_ut'],'fit_rms_ut':c['fit_rms_ut'],'fusion':s,'optical_service':run(['systemctl','is-active','f8-optical.service']).stdout.strip(),'optical_enabled':run(['systemctl','is-enabled','f8-optical.service']).stdout.strip(),'imu_driver':Path('/sys/bus/i2c/devices/3-0068/driver').resolve().name,'compass_driver':Path('/sys/bus/i2c/devices/3-000f/driver').resolve().name,'optical_driver':Path('/sys/bus/i2c/devices/3-0024/driver').resolve().name}))
