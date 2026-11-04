import os,pwd,subprocess,json,time,shutil
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
h='alsa_output.platform-es8388-sound.HiFi__Speaker__sink'
def run(a,check=True):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10)
 if check:assert r.returncode==0,r.stderr
 return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
run(u+['pactl','set-sink-volume',h,'48%'])
run(u+['pactl','set-default-sink',h])
s=json.loads(run(u+['pactl','--format=json','list','sinks'])['stdout']);v=next((x for x in s if x['name']=='f8-speaker-volume'),None)
if v:
 for stream in json.loads(run(u+['pactl','--format=json','list','sink-inputs'])['stdout']):
  if stream['sink']==v['index']:run(u+['pactl','move-sink-input',str(stream['index']),h])
run(u+['systemctl','--user','disable','--now','f8-speaker-volume.service'],False)
run(u+['systemctl','--user','stop','f8-volume-curve-trial.service'],False)
p=Path('/etc/systemd/user/default.target.wants/f8-speaker-volume.service')
if p.is_symlink():p.unlink()
backup=Path('/var/lib/f8-pro/backups/speaker-volume-v1/disabled-r3');backup.mkdir(parents=True,exist_ok=True)
for name in ['/usr/share/f8-pro/audio/f8-speaker-volume.conf','/usr/share/f8-pro/audio/f8-soft-volume.c','/usr/share/f8-pro/audio/ladspa.h','/usr/libexec/f8-pro/speaker-volume-service.py','/etc/systemd/user/f8-speaker-volume.service','/etc/xdg/autostart/f8-speaker-volume.desktop','/usr/lib/f8-pro/f8-soft-volume.so']:
 p=Path(name)
 if p.is_file():
  dest=backup/name.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(p),str(dest))
run(u+['systemctl','--user','daemon-reload'])
run(u+['pactl','set-default-sink',h]);run(u+['pactl','set-sink-volume',h,'48%']);run(u+['pactl','set-sink-mute',h,'0'])
time.sleep(.5)
s=json.loads(run(u+['pactl','--format=json','list','sinks'])['stdout']);assert not any(x['name']=='f8-speaker-volume' for x in s)
hw=next(x for x in s if x['name']==h);assert not hw['mute'] and all(abs(x['value']/65536-.48)<.001 for x in hw['volume'].values())
assert run(u+['pactl','get-default-sink'])['stdout'].strip()==h
print(json.dumps({'restored':True,'default':h,'volume':hw['volume'],'mute':hw['mute'],'remaining_sinks':[x['name'] for x in s],'controls':{n:run(['amixer','-c','0','sget',n]) for n in ['PCM','Output 2','Speaker','OUT2']},'service':run(u+['systemctl','--user','is-enabled','f8-speaker-volume.service'],False),'streams':run(u+['pactl','--format=json','list','sink-inputs'])}))
