import argparse,base64,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--round',choices=['baseline1','p252-1','p157-1','p128-1','p128-2','p122-1','p122-2'],default='baseline1');a=p.parse_args()
files={n:base64.b64encode((P/'armbian/touch'/n).read_bytes()).decode() for n in ['capture-report-rate.py','report-rate-panel.py']}
code='''import base64,json,os,pwd,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
trial=TRIAL
assert not (Path('/var/lib/f8-pro/touch-rate')/trial).exists(),'Preserve earlier data'
base=Path('/usr/local/lib/f8-pro/experimental/touch-rate');base.mkdir(parents=True,exist_ok=True)
for name,data in FILES.items():
 p=base/name;assert not p.is_symlink();p.write_bytes(base64.b64decode(data));p.chmod(0o755)
r=subprocess.run(['systemd-run','--collect','--unit=f8-touch-rate-'+trial,'--property=RuntimeMaxSec=210','/usr/bin/python3',str(base/'capture-report-rate.py'),'--round',trial],capture_output=True,text=True,timeout=10);assert r.returncode==0,r.stderr
time.sleep(1)
status=Path('/run')/('f8-touch-rate-'+trial+'.json');assert status.exists(),'Capture failed to initialize'
state=json.loads(status.read_text());assert state['phase']=='waiting_for_touch',state
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
subprocess.run(u+['systemctl','--user','stop','f8-touch-rate-panel'],capture_output=True,timeout=8)
r=subprocess.run(u+['systemctl','--user','show-environment'],capture_output=True,text=True,timeout=8);assert r.returncode==0
env=[l for l in r.stdout.splitlines() if '=' in l and l.split('=',1)[0] in ['DISPLAY','XAUTHORITY','WAYLAND_DISPLAY']]
r=subprocess.run(u+['systemd-run','--user','--collect','--unit=f8-touch-rate-panel',*['--setenv='+l for l in env],'--setenv=QT_QPA_PLATFORM=wayland','/usr/bin/python3',str(base/'report-rate-panel.py'),'--round',trial],capture_output=True,text=True,timeout=10)
print(json.dumps({'capture':state,'panel_exit':r.returncode,'panel_message':r.stderr,'touch_module_changed':False},indent=2))
'''.replace('TRIAL',repr(a.round)).replace('FILES',repr(files))
compile(code,'capture-runner','exec');(P/('local/hardware/touch-rate-'+a.round+'-runner.py')).write_text(code)
print('Capture payload prepared: '+a.round)
