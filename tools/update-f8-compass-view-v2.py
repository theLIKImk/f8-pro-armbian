"""Update compass labels and calibration quality checks; preserve user calibration."""
import base64,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'local/hardware/compass-app';assert not (out/'update02.json').exists()
encoded=base64.b64encode((P/'armbian/motion/compass-view.py').read_bytes()).decode()
code='''import ast,base64,hashlib,json,subprocess
from pathlib import Path
path=Path('/usr/local/lib/f8-pro/compass-view.py');old=path.read_bytes()
assert hashlib.sha256(old).hexdigest()=='8000f27f726af3599c918f5ed090c0220b4f03e7cac6be2b63fad132294a0c7f'
data=base64.b64decode(PAYLOAD);ast.parse(data.decode())
backup=Path('/var/lib/f8-pro/compass-view-v2');backup.mkdir(exist_ok=False)
(backup/'compass-view-before.py').write_bytes(old)
cal=Path('/home/f8test/.config/f8-pro/compass-calibration.json')
before_cal=cal.read_bytes() if cal.exists() else None
if before_cal:(backup/'calibration-before.json').write_bytes(before_cal)
prefix=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus']
def user(args,check=True):
 p=subprocess.run(prefix+args,capture_output=True,text=True,timeout=15)
 if check:assert p.returncode==0,(args,p.stdout,p.stderr)
 return p
try:
 path.write_bytes(data);path.chmod(0o755)
 preview=Path('/home/f8test/.cache/f8-compass/update02-preview.png')
 rendered=user(['env','QT_QPA_PLATFORM=offscreen','/usr/local/bin/f8-compass','--preview',str(preview)])
 active=user(['systemctl','--user','is-active','f8-compass-view.service'],False).returncode==0
 if active:user(['systemctl','--user','restart','f8-compass-view.service'])
 else:
  sockets=[p.name for p in Path('/run/user/1601').glob('wayland-*') if p.is_socket()];assert sockets
  user(['systemd-run','--user','--collect','--unit=f8-compass-view','--setenv=QT_QPA_PLATFORM=wayland','--setenv=WAYLAND_DISPLAY='+sockets[0],'/usr/local/bin/f8-compass'])
 status=user(['systemctl','--user','is-active','f8-compass-view.service']).stdout.strip()
 assert (cal.read_bytes() if cal.exists() else None)==before_cal,'Calibration unexpectedly changed'
 print(json.dumps({'success':True,'file_sha256':hashlib.sha256(data).hexdigest(),'backup':str(backup),
  'old_calibration_preserved':True,'launch_status':status,'preview_stderr':rendered.stderr,
  'preview_png_base64':base64.b64encode(preview.read_bytes()).decode()},indent=2))
except Exception:
 path.write_bytes(old);path.chmod(0o755);user(['systemctl','--user','restart','f8-compass-view.service'],False);raise
'''.replace('PAYLOAD',repr(encoded))
runner=out/'update02-runner.sh';assert not runner.exists();runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-2000:]
d=json.loads(r.stdout);(out/'update02-preview.png').write_bytes(base64.b64decode(d.pop('preview_png_base64')))
(out/'update02.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
