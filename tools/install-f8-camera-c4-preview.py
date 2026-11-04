"""Install a user-launched preview and isolated AIQ worker, no boot autostart."""
import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
files={
 '/usr/local/lib/f8-pro/aiq-backend.py':((P/'armbian/camera/aiq-backend.py').read_bytes(),0o755),
 '/usr/local/lib/f8-pro/camera-preview.py':((P/'armbian/camera/camera-preview.py').read_bytes(),0o755),
 '/usr/local/bin/f8-camera-preview':(b'#!/bin/sh\nexec /usr/bin/python3 /usr/local/lib/f8-pro/camera-preview.py "$@"\n',0o755),
}
desktop='[Desktop Entry]\nType=Application\nName=F8 Camera Preview\nName[zh_CN]=F8 相机预览\nExec=/usr/local/bin/f8-camera-preview\nIcon=camera-photo\nTerminal=false\nCategories=AudioVideo;Video;\n'
files['/usr/share/applications/f8-camera-preview.desktop']=(desktop.encode(),0o644)
files['/home/f8test/Desktop/f8-camera-preview.desktop']=(desktop.encode(),0o755)
for path,(data,_) in files.items():
 if path.endswith('.py'):compile(data,path,'exec')
payload={n:{'data':base64.b64encode(b).decode(),'mode':m,'sha256':hashlib.sha256(b).hexdigest()} for n,(b,m) in files.items()}
code='''import base64,hashlib,json,os,pwd,subprocess
from pathlib import Path
assert Path('/sys/firmware/devicetree/base/chosen/f8-camera-async-trial').read_bytes()==b'c4\\0'
payload=PAYLOAD
for n in payload:assert not Path(n).exists(),n
for n,v in payload.items():
 p=Path(n);p.parent.mkdir(parents=True,exist_ok=True);data=base64.b64decode(v['data'])
 if n.endswith('.py'):compile(data,n,'exec')
 p.write_bytes(data);p.chmod(v['mode']);assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
 if n.startswith('/home/f8test/'):
  u=pwd.getpwnam('f8test');os.chown(p,u.pw_uid,u.pw_gid)
r=subprocess.run(['desktop-file-validate','/usr/share/applications/f8-camera-preview.desktop'],capture_output=True,text=True,timeout=8)
assert r.returncode==0,r.stderr
print(json.dumps({'installed':{n:v['sha256'] for n,v in payload.items()},'autostart':False,'launch_requested':False},indent=2))
'''.replace('PAYLOAD',repr(payload))
runner=P/'local/hardware/camera-c4-preview-install-runner.sh';assert not runner.exists()
runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=90)
assert r.returncode==0,r.stderr
(P/'local/hardware/camera-c4-preview-install01.json').write_text(r.stdout)
print(r.stdout)
