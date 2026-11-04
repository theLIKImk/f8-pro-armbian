import json,os,pwd,re,shutil,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
uid=pwd.getpwnam('likimk').pw_uid;app=Path('/home/likimk/Applications/Phira-linux-arm64-v0.8.2')
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/'+str(uid),'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/'+str(uid)+'/bus']
def run(a):
 try:
  r=subprocess.run(a,capture_output=True,text=True,timeout=10);return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 except (OSError,subprocess.TimeoutExpired) as e:return {'error':str(e)}
o={};s=run(u+['systemctl','--user','show-environment']);keys=['DISPLAY','XAUTHORITY','WAYLAND_DISPLAY'];env=[l for l in s.get('stdout','').splitlines() if '=' in l and l.split('=',1)[0] in keys];x=u+['env',*env]
o['tools']={n:shutil.which(n) for n in ['kdialog','zenity','qarma','yad','xinput','xprop','pactl','wpctl']}
p=app/'data/data.json'
if p.exists():
 d=json.loads(p.read_text());c=d.get('config',{});o['audio_config']={k:v for k,v in c.items() if any(t in k.lower() for t in ['volume','audio','sample','bgm','music'])}
o['service']=run(u+['systemctl','--user','show','f8-phira-arm64','-p','ActiveState','-p','MainPID'])
pid=next((int(l.split('=',1)[1]) for l in o['service'].get('stdout','').splitlines() if l.startswith('MainPID=')),0)
o['default_sink']=run(u+['pactl','get-default-sink'])
for kind in ['sink-inputs','sinks']:
 r=run(u+['pactl','--format=json','list',kind])
 if r.get('exit')==0:
  values=json.loads(r['stdout'])
  if kind=='sink-inputs':values=[v for v in values if str(pid)==v.get('properties',{}).get('application.process.id') or 'phira' in json.dumps(v.get('properties',{})).lower()]
  o[kind]=[{k:v.get(k) for k in ['index','name','sink','mute','volume','sample_specification','channel_map','state','active_port']}|{'application':{k:v.get('properties',{}).get(k) for k in ['application.name','application.process.binary','application.process.id','media.name']}} for v in values]
 else:o[kind]=r
o['alsa_cards']=Path('/proc/asound/cards').read_text();o['alsa_pcm_status']={str(p):p.read_text() for p in Path('/proc/asound').glob('card*/pcm*p/sub*/status')}
o['active_window']=run(x+['xprop','-root','_NET_ACTIVE_WINDOW'])
o['phira_window']=run(x+['xprop','-name','Phira','_NET_WM_PID','_NET_WM_STATE','WM_CLASS'])
if shutil.which('xinput'):o['xinput']=run(x+['xinput','list','--short'])
o['log_errors']=[]
for p in (app/'data/logs').glob('*.log'):
 for l in p.read_text(errors='replace').splitlines():
  if ('WARN' in l or 'ERROR' in l) and any(t in l.lower() for t in ['audio','alsa','cpal','input box','get input','sound','backend']):o['log_errors'].append(l)
o['log_errors']=o['log_errors'][-25:]
print(json.dumps(o,indent=2))
