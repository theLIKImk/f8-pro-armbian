import os,pwd,subprocess,json,time,math,array
from pathlib import Path
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);assert r.returncode==0,r.stderr;return r.stdout
subprocess.run(u+['systemctl','--user','stop','f8-volume-curve-trial.service'],capture_output=True)
mid=run(u+['pactl','load-module','module-null-sink','sink_name=f8-curve-test-null']).strip()
p=Path('/run/f8-volume-curve-trial.conf');original=Path('/usr/share/f8-pro/audio/f8-speaker-volume.conf').read_text();p.write_text(original.replace('alsa_output.platform-es8388-sound.HiFi__Speaker__sink','f8-curve-test-null'))
o={}
run(u+['systemctl','--user','stop','f8-speaker-volume.service'])
try:
 run(u+['systemd-run','--user','--unit=f8-volume-curve-trial','--collect','/usr/bin/pipewire','-c',str(p)]);time.sleep(1)
 tone=array.array('f',(0.1*math.sin(2*math.pi*440*i/48000) for i in range(96000) for ch in range(2))).tobytes()
 for n in [0,10,20,30,100]:
  run(u+['pactl','set-sink-volume','f8-speaker-volume',f'{n}%'])
  rec=subprocess.Popen(u+['parec','--device=f8-curve-test-null.monitor','--format=float32le','--rate=48000','--channels=2'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  play=subprocess.Popen(u+['pw-cat','--playback','--raw','--target=f8-speaker-volume','--rate=48000','--channels=2','--format=f32','-'],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  play.communicate(tone,timeout=5);time.sleep(.1);rec.terminate();raw,err=rec.communicate(timeout=3)
  a=array.array('f');a.frombytes(raw[:len(raw)//4*4]);peak=max(map(abs,a),default=0)
  o[n]=dict(peak=peak,expected=(.1*(n/100)**1.5),samples=len(a))
  assert abs(peak-(.1*(n/100)**1.5))<.0001,str(o)
finally:
 run(u+['systemctl','--user','stop','f8-volume-curve-trial.service']);p.write_text(original)
 run(u+['pactl','unload-module',mid])
 run(u+['systemctl','--user','start','f8-speaker-volume.service'])
print(json.dumps(o))
