import os,pwd,subprocess,json,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);assert r.returncode==0,r.stderr;return r.stdout
# No application currently plays into the old physical sink.
s=json.loads(run(u+['pactl','--format=json','list','sink-inputs']))
assert all((x.get('properties',{}).get('node.name')=='f8-speaker-volume-output' or x.get('corked')) for x in s),s
run(u+['pactl','set-sink-volume','f8-speaker-volume','20%']);time.sleep(1.5)
run(u+['systemctl','--user','stop','f8-speaker-volume.service'])
s=json.loads(run(u+['pactl','--format=json','list','sinks']));h=next(x for x in s if x['name'].startswith('alsa_output.platform-es8388'))
assert all(abs(v['value']/65536-(.2**.5))<.001 for v in h['volume'].values()),h['volume']
o={'stopped_physical_volume':h['volume']}
run(u+['systemctl','--user','start','f8-speaker-volume.service']);time.sleep(2)
s=json.loads(run(u+['pactl','--format=json','list','sinks']));v=next(x for x in s if x['name']=='f8-speaker-volume');h=next(x for x in s if x['name'].startswith('alsa_output.platform-es8388'))
assert all(abs(x['value']/65536-.2)<.001 for x in v['volume'].values()),v['volume']
assert all(x['value']==65536 for x in h['volume'].values()),h['volume']
assert run(u+['pactl','get-default-sink']).strip()=='f8-speaker-volume'
run(u+['pactl','set-sink-mute','f8-speaker-volume','1']);time.sleep(1.2)
run(u+['systemctl','--user','restart','f8-speaker-volume.service']);time.sleep(2)
s=json.loads(run(u+['pactl','--format=json','list','sinks']));assert next(x for x in s if x['name']=='f8-speaker-volume')['mute']
run(u+['pactl','set-sink-mute','f8-speaker-volume','0'])
p=Path('/etc/systemd/user/default.target.wants/f8-speaker-volume.service');p.parent.mkdir(parents=True,exist_ok=True)
if not p.exists():p.symlink_to('../f8-speaker-volume.service')
o.update(restart_volume_preserved=True,restart_mute_preserved=True,default=run(u+['pactl','get-default-sink']),service=run(u+['systemctl','--user','is-active','f8-speaker-volume.service']),current_percent=20,output2=run(['amixer','-c','0','sget','Output 2']))
print(json.dumps(o))
