import collections,json,os,pwd,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
r=subprocess.run(u+['journalctl','--user','-b','-u','f8-phira-arm64','--no-pager','-o','cat','-n','400'],capture_output=True,text=True,timeout=10)
lines=[l for l in r.stdout.splitlines() if l.startswith('Phira F8:')]
o={'xi2_enabled':any('XInput2 touch and pointer events enabled' in l for l in lines),'touch_diagnostics':lines[-35:],'journal_exit':r.returncode,'journal_stderr':r.stderr,'journal_lines':len(r.stdout.splitlines())}
r=subprocess.run(['journalctl','-b','_SYSTEMD_USER_UNIT=f8-phira-arm64.service','--no-pager','-o','cat','-n','150'],capture_output=True,text=True,timeout=10)
o['startup_diagnostics']=[l for l in r.stdout.splitlines() if any(t in l for t in ['Phira F8:','panicked','Main process exited','Failed with result','ALSA lib','X Error','BadAccess','BadValue'])][-40:]
r=subprocess.run(u+['systemctl','--user','show','f8-phira-arm64','-p','MainPID','-p','ActiveState','-p','Result','-p','ExecMainStatus','-p','ExecMainCode'],capture_output=True,text=True,timeout=8);o['service']=r.stdout
pid=next((int(l.split('=',1)[1]) for l in r.stdout.splitlines() if l.startswith('MainPID=')),0)
if pid:
 o['drm']=[]
 for f in Path('/proc',str(pid),'fdinfo').glob('*'):
  try:
   v=[l for l in f.read_text().splitlines() if l.startswith('drm-driver:')]
   o['drm'].extend(v)
  except OSError:pass
r=subprocess.run(u+['journalctl','--user','-u','f8-phira-input-demo','-o','cat','--no-pager','-n','10'],capture_output=True,text=True,timeout=8)
o['qt_demo_count_only']=[l for l in r.stdout.splitlines() if l.startswith('{') and 'characters' in l]
print(json.dumps(o,indent=2))
