import json,os,subprocess,wave
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
p=Path('/home/likimk/.cache/f8-mic-check-20261102/results.json')
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
r=subprocess.run(u+['systemctl','--user','status','f8-mic-check-r1.service','--no-pager'],capture_output=True,text=True,timeout=10)
j=subprocess.run(u+['journalctl','--user','-u','f8-mic-check-r1.service','-n','45','--no-pager'],capture_output=True,text=True,timeout=10)
sysj=subprocess.run(['journalctl','-u','user@1602.service','-n','55','--no-pager'],capture_output=True,text=True,timeout=10)
files=[]
for wav in p.parent.glob('*.wav'):
 try:
  with wave.open(str(wav),'rb') as w:files.append({'file':wav.name,'duration':w.getnframes()/w.getframerate(),'frames':w.getnframes(),'bytes':wav.stat().st_size})
 except Exception as e:files.append({'file':wav.name,'error':str(e)})
print(json.dumps({'results':json.loads(p.read_text()) if p.exists() else None,'files':files,'gui':r.stdout,'errors':r.stderr,'journal':j.stdout,'system_user_journal':sysj.stdout},indent=2))
