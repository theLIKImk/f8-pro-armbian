import os,pwd,subprocess,json
from pathlib import Path
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
o={'template':Path('/usr/share/pipewire/filter-chain.conf').read_text(),'services':run(u+['systemctl','--user','list-units','--type=service','--no-pager'])}
o['sinks']=run(u+['pactl','--format=json','list','sinks']);o['inputs']=run(u+['pactl','--format=json','list','sink-inputs'])
print(json.dumps(o))
