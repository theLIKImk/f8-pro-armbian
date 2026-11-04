import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
files={'/usr/local/bin/f8-chromium-camera':((P/'armbian/camera/chromium-camera-launch.py').read_bytes(),0o755),'/usr/local/share/f8-pro/camera-browser-test.html':((P/'armbian/camera/camera-browser-test.html').read_bytes(),0o644)}
desktop='[Desktop Entry]\nType=Application\nName=Chromium Camera Compatible\nName[zh_CN]=Chromium（相机兼容）\nExec=/usr/local/bin/f8-chromium-camera %U\nIcon=chromium\nTerminal=false\nCategories=Network;WebBrowser;\n'
for p,m in [('/usr/share/applications/f8-chromium-camera.desktop',0o644),('/home/f8test/Desktop/f8-chromium-camera.desktop',0o755)]:files[p]=(desktop.encode(),m)
payload={n:{'data':base64.b64encode(d).decode(),'mode':m,'hash':hashlib.sha256(d).hexdigest()} for n,(d,m) in files.items()}
code='''import base64,hashlib,json,os,pwd,subprocess
from pathlib import Path
files=PAYLOAD
for n in files:assert not Path(n).exists(),n
for n,v in files.items():
 p=Path(n);p.parent.mkdir(parents=True,exist_ok=True);d=base64.b64decode(v['data']);assert hashlib.sha256(d).hexdigest()==v['hash']
 if n.endswith('f8-chromium-camera'):compile(d,n,'exec')
 p.write_bytes(d);p.chmod(v['mode'])
 if n.startswith('/home/f8test/'):
  u=pwd.getpwnam('f8test');os.chown(p,u.pw_uid,u.pw_gid)
subprocess.run(['desktop-file-validate','/usr/share/applications/f8-chromium-camera.desktop'],check=True)
print(json.dumps({'installed':{n:v['hash'] for n,v in files.items()},'separate_profile':True,'sandbox_disabled':False,'automatic_permission_grant':False},indent=2))
'''.replace('PAYLOAD',repr(payload))
runner=P/'local/hardware/camera-chromium-install01-runner.sh';assert not runner.exists();runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=90);assert r.returncode==0,r.stderr
(P/'local/hardware/camera-chromium-install01.json').write_text(r.stdout);print(r.stdout)
