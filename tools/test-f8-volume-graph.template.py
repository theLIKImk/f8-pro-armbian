import os,pwd,subprocess,json,time,base64
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
def run(a,check=True):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10)
 if check and r.returncode:raise RuntimeError(r.stderr)
 return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
p=Path('/run/f8-volume-curve-trial.conf');p.write_bytes(base64.b64decode('PAYLOAD'))
run(u+['systemd-run','--user','--unit=f8-volume-curve-trial','--collect','/usr/bin/pipewire','-c',str(p)])
time.sleep(2)
s=json.loads(run(u+['pactl','--format=json','list','sinks'])['stdout']);v=next(x for x in s if x['name']=='f8-speaker-volume')
o={'sink':v,'checks':{}}
for percent in [0,10,30,100]:
 run(u+['pactl','set-sink-volume',v['name'],f'{percent}%']);time.sleep(.2)
 o['checks'][percent]=run(u+['pw-cli','enum-params',str(v['properties']['object.id']),'Props'])
run(u+['pactl','set-sink-volume',v['name'],'11%'])
print(json.dumps(o))
