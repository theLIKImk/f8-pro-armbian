import os,pwd,subprocess,json,time,re
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);assert r.returncode==0,r.stderr;return r.stdout
s=json.loads(run(u+['pactl','--format=json','list','sinks']));v=next(x for x in s if x['name']=='f8-speaker-volume')
p=subprocess.Popen(u+['pw-cat','--playback','--raw','--target=f8-speaker-volume','--rate=48000','--channels=2','--format=f32','/dev/zero'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
o={}
try:
 time.sleep(1)
 assert p.poll() is None,p.stderr.read().decode()
 for n in [0,10,20,30,100]:
  run(u+['pactl','set-sink-volume','f8-speaker-volume',f'{n}%']);time.sleep(.3)
  t=run(u+['pw-cli','enum-params',v['properties']['object.id'],'Props'])
  vals=re.findall(r'String "((?:left|right):Gain 1)"\s+Float ([-.\d]+)',t)
  o[n]=vals
  assert len(vals)==2 and all(abs(float(x[1])-n/100)<.0001 for x in vals),str((n,vals))
finally:
 run(u+['pactl','set-sink-volume','f8-speaker-volume','11%'])
 p.terminate();p.wait(timeout=3)
print(json.dumps(o))

