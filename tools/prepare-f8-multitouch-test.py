import base64,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];a=P/'armbian/touch'
files={name:base64.b64encode((a/name).read_bytes()).decode() for name in ['multitouch-test.py','f8-multitouch.desktop']}
code='''import base64,json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
files=json.loads(base64.b64decode(DATA))
for name,dest,mode in [('multitouch-test.py','/usr/local/lib/f8-pro/multitouch-test.py',0o755),('f8-multitouch.desktop','/usr/share/applications/f8-multitouch.desktop',0o644)]:
 p=Path(dest);assert not p.is_symlink();p.write_bytes(base64.b64decode(files[name]));p.chmod(mode);os.chown(p,0,0)
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus','WAYLAND_DISPLAY=wayland-0','QT_QPA_PLATFORM=wayland']
check=subprocess.run(u+['/usr/bin/python3','-c','from PyQt6.QtGui import QEventPoint; print(QEventPoint.State.Released)'],capture_output=True,text=True,timeout=8);assert check.returncode==0,check.stderr
subprocess.run(u+['systemctl','--user','stop','f8-multitouch-test.service'],capture_output=True,timeout=8)
r=subprocess.run(u+['systemd-run','--user','--collect','--unit=f8-multitouch-test','/usr/bin/python3','/usr/local/lib/f8-pro/multitouch-test.py'],capture_output=True,text=True,timeout=8)
print(json.dumps({'exit':r.returncode,'message':r.stderr,'qt_import':check.stdout}))
'''.replace('DATA',repr(base64.b64encode(json.dumps(files).encode()).decode()))
(P/'local/hardware/multitouch-install-runner.py').write_text(code)
