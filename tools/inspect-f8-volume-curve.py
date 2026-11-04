import json,os,pwd,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
o={'versions':run(['dpkg-query','-W','pipewire','wireplumber','libspa-0.2-modules']),'controls':{n:run(['amixer','-c','0','sget',n]) for n in ['PCM','Output 2','Speaker']}}
o['default_sink']=run(u+['pactl','get-default-sink'])
r=run(u+['pactl','--format=json','list','sinks'])
if r['exit']==0:
 o['sinks']=[{k:s.get(k) for k in ['name','index','mute','volume','base_volume','active_port','sample_specification']} for s in json.loads(r['stdout'])]
o['settings']=run(u+['wpctl','settings'])
configs={}
for base in ['/etc/wireplumber','/etc/pipewire','/home/likimk/.config/wireplumber','/home/likimk/.config/pipewire']:
 for p in Path(base).rglob('*'):
  if p.is_file() and p.suffix in ['.conf','.lua'] and p.stat().st_size<32768:
   text=p.read_text(errors='replace')
   if any(x in text.lower() for x in ['volume','ucm','soft-mixer']):configs[str(p)]=text
o['configs']=configs
print(json.dumps(o,indent=2))
