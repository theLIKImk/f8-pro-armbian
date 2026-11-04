import os,pwd,subprocess,json
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
print(json.dumps({'default':run(u+['pactl','get-default-sink']),'sinks':run(u+['pactl','--format=json','list','sinks']),'streams':run(u+['pactl','--format=json','list','sink-inputs']),'service':run(u+['journalctl','--user','-u','f8-speaker-volume.service','-n','18','--no-pager']),'controls':{n:run(['amixer','-c','0','sget',n]) for n in ['PCM','Output 2','Speaker','OUT2']},'state':run(u+['cat',f'/home/likimk/.local/state/f8-speaker-volume/state.json'])}))
