import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
files={
 '/usr/local/lib/f8-pro/cover-screen.py':((P/'armbian/input/cover-screen.py').read_bytes(),0o755),
 '/usr/local/lib/f8-pro/cover-haptic-test.py':((P/'armbian/input/cover-haptic-test.py').read_bytes(),0o755),
 '/usr/local/bin/f8-cover-test':(b'#!/bin/sh\nexec /usr/bin/python3 /usr/local/lib/f8-pro/cover-haptic-test.py\n',0o755),
 '/home/f8test/.config/f8-cover.json':(b'{"validated":false,"screen_enabled":false}\n',0o644),
 '/home/f8test/.config/systemd/user/f8-cover-screen.service':(b'[Unit]\nDescription=F8 magnetic cover screen control\nPartOf=graphical-session.target\n\n[Service]\nExecStart=/usr/bin/python3 /usr/local/lib/f8-pro/cover-screen.py\nRestart=on-failure\nRestartSec=3\n\n[Install]\nWantedBy=graphical-session.target\n',0o644)}
desktop='[Desktop Entry]\nType=Application\nName=F8 Cover and Haptic Test\nName[zh_CN]=F8 霍尔与振动测试\nExec=/usr/local/bin/f8-cover-test\nIcon=preferences-desktop-peripherals\nTerminal=false\nCategories=System;\n'
for n,m in [('/usr/share/applications/f8-cover-test.desktop',0o644),('/home/f8test/Desktop/f8-cover-test.desktop',0o755)]:files[n]=(desktop.encode(),m)
for n,(d,m) in files.items():
 if n.endswith('.py'):compile(d,n,'exec')
payload={n:{'data':base64.b64encode(d).decode(),'mode':m,'hash':hashlib.sha256(d).hexdigest()} for n,(d,m) in files.items()}
code='''import base64,hashlib,json,os,pwd,subprocess
from pathlib import Path
files=PAYLOAD
for n in files:assert not Path(n).exists(),n
for n,v in files.items():
 p=Path(n);p.parent.mkdir(parents=True,exist_ok=True);d=base64.b64decode(v['data']);assert hashlib.sha256(d).hexdigest()==v['hash'];p.write_bytes(d);p.chmod(v['mode'])
 if n.startswith('/home/f8test/'):
  u=pwd.getpwnam('f8test');os.chown(p,u.pw_uid,u.pw_gid)
u=pwd.getpwnam('f8test')
for n in ['/home/f8test/.config/systemd','/home/f8test/.config/systemd/user']:os.chown(n,u.pw_uid,u.pw_gid)
old=Path('/etc/udev/rules.d/99-f8-cover-haptic.rules');new=Path('/etc/udev/rules.d/70-f8-cover-haptic.rules');assert not new.exists() and 'F8 Hall Cover' in old.read_text() and 'F8 Haptic Motor' in old.read_text();old.rename(new)
subprocess.run(['udevadm','control','--reload-rules'],check=True,timeout=8)
for p in Path('/sys/class/input').glob('event*'):
 if (p/'device/name').read_text().strip() in ['F8 Hall Cover','F8 Haptic Motor']:subprocess.run(['udevadm','trigger','--action=change',str(p)],check=True,timeout=8)
subprocess.run(['udevadm','settle','--timeout=8'],check=True,timeout=10)
subprocess.run(['desktop-file-validate','/usr/share/applications/f8-cover-test.desktop'],check=True)
print(json.dumps({'files':{n:v['hash'] for n,v in files.items()},'policy':'observe only, no screen changes yet'},indent=2))
'''.replace('PAYLOAD',repr(payload))
runner=P/'local/hardware/hall-haptic-session-install01-runner.sh';assert not runner.exists();runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=90);assert r.returncode==0,r.stdout+r.stderr
(P/'local/hardware/hall-haptic-session-install01.json').write_text(r.stdout);print(r.stdout)
