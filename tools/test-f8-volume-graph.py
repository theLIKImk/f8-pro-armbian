import os,pwd,subprocess,json,time,base64
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
def run(a,check=True):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10)
 if check and r.returncode:raise RuntimeError(r.stderr)
 return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
p=Path('/run/f8-volume-curve-trial.conf');p.write_bytes(base64.b64decode('Y29udGV4dC5wcm9wZXJ0aWVzID0geyBsb2cubGV2ZWwgPSAyIH0KY29udGV4dC5zcGEtbGlicyA9IHsgYXVkaW8uY29udmVydC4qID0gYXVkaW9jb252ZXJ0L2xpYnNwYS1hdWRpb2NvbnZlcnQgc3VwcG9ydC4qID0gc3VwcG9ydC9saWJzcGEtc3VwcG9ydCB9CmNvbnRleHQubW9kdWxlcyA9IFsKIHsgbmFtZSA9IGxpYnBpcGV3aXJlLW1vZHVsZS1wcm90b2NvbC1uYXRpdmUgfQogeyBuYW1lID0gbGlicGlwZXdpcmUtbW9kdWxlLWNsaWVudC1ub2RlIH0KIHsgbmFtZSA9IGxpYnBpcGV3aXJlLW1vZHVsZS1hZGFwdGVyIH0KIHsgbmFtZSA9IGxpYnBpcGV3aXJlLW1vZHVsZS1maWx0ZXItY2hhaW4KICAgYXJncyA9IHsKICAgIG5vZGUuZGVzY3JpcHRpb24gPSAiRjggU3BlYWtlcnMiCiAgICBtZWRpYS5uYW1lID0gIkY4IFNwZWFrZXIgVm9sdW1lIEN1cnZlIgogICAgZmlsdGVyLmdyYXBoID0gewogICAgIG5vZGVzID0gWwogICAgICB7IHR5cGUgPSBidWlsdGluIG5hbWUgPSBsZWZ0IGxhYmVsID0gbWl4ZXIgY29udHJvbCA9IHsgIkdhaW4gMSIgPSAwLjAgfSB9CiAgICAgIHsgdHlwZSA9IGJ1aWx0aW4gbmFtZSA9IHJpZ2h0IGxhYmVsID0gbWl4ZXIgY29udHJvbCA9IHsgIkdhaW4gMSIgPSAwLjAgfSB9CiAgICAgXQogICAgIGlucHV0cyA9IFsgImxlZnQ6SW4gMSIgInJpZ2h0OkluIDEiIF0KICAgICBvdXRwdXRzID0gWyAibGVmdDpPdXQiICJyaWdodDpPdXQiIF0KICAgICBjYXB0dXJlLnZvbHVtZXMgPSBbCiAgICAgIHsgY29udHJvbCA9ICJsZWZ0OkdhaW4gMSIgbWluID0gMC4wIG1heCA9IDEuMCBzY2FsZSA9IGN1YmljIH0KICAgICAgeyBjb250cm9sID0gInJpZ2h0OkdhaW4gMSIgbWluID0gMC4wIG1heCA9IDEuMCBzY2FsZSA9IGN1YmljIH0KICAgICBdCiAgICB9CiAgICBhdWRpby5jaGFubmVscyA9IDIKICAgIGF1ZGlvLnBvc2l0aW9uID0gWyBGTCBGUiBdCiAgICBjYXB0dXJlLnByb3BzID0gewogICAgIG5vZGUubmFtZSA9IGY4LXNwZWFrZXItdm9sdW1lCiAgICAgbm9kZS5kZXNjcmlwdGlvbiA9ICJGOCBTcGVha2VycyIKICAgICBtZWRpYS5jbGFzcyA9IEF1ZGlvL1NpbmsKICAgICBwcmlvcml0eS5zZXNzaW9uID0gMTEwMAogICAgIG5vZGUudmlydHVhbCA9IHRydWUKICAgICB2b2x1bWUgPSAwLjAwMTM1MgogICAgfQogICAgcGxheWJhY2sucHJvcHMgPSB7CiAgICAgbm9kZS5uYW1lID0gZjgtc3BlYWtlci12b2x1bWUtb3V0cHV0CiAgICAgbm9kZS5wYXNzaXZlID0gdHJ1ZQogICAgIHRhcmdldC5vYmplY3QgPSAiYWxzYV9vdXRwdXQucGxhdGZvcm0tZXM4Mzg4LXNvdW5kLkhpRmlfX1NwZWFrZXJfX3NpbmsiCiAgICAgc3RyZWFtLmRvbnQtcmVtaXggPSB0cnVlCiAgICB9CiAgIH0KIH0KXQ0K'))
run(u+['systemd-run','--user','--unit=f8-volume-curve-trial','--collect','/usr/bin/pipewire','-c',str(p)])
time.sleep(2)
s=json.loads(run(u+['pactl','--format=json','list','sinks'])['stdout']);v=next(x for x in s if x['name']=='f8-speaker-volume')
o={'sink':v,'checks':{}}
for percent in [0,10,30,100]:
 run(u+['pactl','set-sink-volume',v['name'],f'{percent}%']);time.sleep(.2)
 o['checks'][percent]=run(u+['pw-cli','enum-params',str(v['properties']['object.id']),'Props'])
run(u+['pactl','set-sink-volume',v['name'],'11%'])
print(json.dumps(o))
