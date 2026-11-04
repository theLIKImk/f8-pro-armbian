"""Install the desktop viewer, render a real empty/device state, then launch once."""
import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'local/hardware/motion-app';out.mkdir(exist_ok=True)
assert not (out/'install01.json').exists()
files={'/usr/local/lib/f8-pro/sensor-monitor.py':((P/'armbian/motion/sensor-monitor.py').read_bytes(),0o755),
 '/usr/local/bin/f8-sensors':(b'#!/bin/sh\nexec /usr/bin/python3 /usr/local/lib/f8-pro/sensor-monitor.py "$@"\n',0o755),
 '/usr/local/share/applications/f8-sensors.desktop':((P/'armbian/motion/f8-sensors.desktop').read_bytes(),0o644)}
payload={name:{'data':base64.b64encode(data).decode(),'mode':mode,'sha256':hashlib.sha256(data).hexdigest()} for name,(data,mode) in files.items()}
code='''import ast,base64,hashlib,json,os,pwd,socket,subprocess
from pathlib import Path
import PyQt6.QtWidgets
payload=PAYLOAD
for name in payload:assert not Path(name).exists() and not Path(name).is_symlink(),name
ast.parse(base64.b64decode(payload['/usr/local/lib/f8-pro/sensor-monitor.py']['data']).decode())
account=pwd.getpwnam('f8test');assert account.pw_uid==1601
prefix=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus']
def user(args,timeout=15):
 r=subprocess.run(prefix+args,capture_output=True,text=True,timeout=timeout)
 assert r.returncode==0,(args,r.stdout,r.stderr)
 return r
created=[]
try:
 for name,v in payload.items():
  p=Path(name);p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(base64.b64decode(v['data']));p.chmod(v['mode']);created.append(p)
  assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
 user(['desktop-file-validate','/usr/local/share/applications/f8-sensors.desktop'])
 desktop=Path(user(['xdg-user-dir','DESKTOP']).stdout.strip())
 assert desktop.is_relative_to(Path(account.pw_dir)) and desktop!=Path(account.pw_dir)
 user(['mkdir','-p',str(desktop)])
 shortcut=desktop/'f8-sensors.desktop';assert not shortcut.exists()
 shortcut.write_bytes(Path('/usr/local/share/applications/f8-sensors.desktop').read_bytes());shortcut.chmod(0o755);os.chown(shortcut,account.pw_uid,account.pw_gid);created.append(shortcut)
 cache=Path(account.pw_dir)/'.cache/f8-sensors';user(['mkdir','-p',str(cache)])
 preview=cache/'install-preview.png'
 rendered=user(['env','QT_QPA_PLATFORM=offscreen','/usr/local/bin/f8-sensors','--preview',str(preview)],timeout=15)
 assert preview.is_file() and preview.read_bytes().startswith(b'\\x89PNG')
 # A standalone user transient unit lets the user close the viewer normally.
 sockets=[p for p in Path('/run/user/1601').glob('wayland-*') if p.is_socket()]
 assert sockets,'Wayland session unavailable'
 launched=user(['systemd-run','--user','--collect','--unit=f8-sensor-monitor','--setenv=WAYLAND_DISPLAY='+sockets[0].name,
  '--setenv=QT_QPA_PLATFORM=wayland','/usr/local/bin/f8-sensors'])
 status=user(['systemctl','--user','is-active','f8-sensor-monitor.service'])
 print(json.dumps({'success':True,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
  'files':{k:v['sha256'] for k,v in payload.items()},'desktop_shortcut':str(shortcut),
  'preview_stderr':rendered.stderr,'launch_status':status.stdout.strip(),'preview_png_base64':base64.b64encode(preview.read_bytes()).decode(),
  'dependencies_already_present':True,'autostart_installed':False,'root_required_to_run':False},indent=2))
except Exception:
 for p in reversed(created):p.unlink(missing_ok=True)
 raise
'''.replace('PAYLOAD',repr(payload))
runner=out/'install01-runner.sh';assert not runner.exists();runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-2500:]
d=json.loads(r.stdout);png=base64.b64decode(d.pop('preview_png_base64'));(out/'install-preview.png').write_bytes(png)
(out/'install01.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(json.dumps(d,ensure_ascii=False,indent=2))
