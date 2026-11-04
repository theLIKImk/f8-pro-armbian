import json,os,pwd,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
r=subprocess.run(u+['systemctl','--user','show-environment'],capture_output=True,text=True,timeout=8);assert r.returncode==0
env=[l for l in r.stdout.splitlines() if '=' in l and l.split('=',1)[0] in ['DISPLAY','XAUTHORITY','WAYLAND_DISPLAY']]
a=Path('/home/likimk/Applications/Phira-linux-arm64-v0.8.2');assert (a/'phira-input.py').is_file()
r=subprocess.run(u+['systemd-run','--user','--collect','--unit=f8-phira-input-demo',*['--setenv='+l for l in env],'--setenv=QT_QPA_PLATFORM=wayland','/usr/bin/python3',str(a/'phira-input.py'),'--demo'],capture_output=True,text=True,timeout=10)
print(json.dumps({'exit':r.returncode,'message':r.stderr}))
