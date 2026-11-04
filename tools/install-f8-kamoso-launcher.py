"""Install a user launcher and first-use device selection; no camera autostart."""
import base64,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
data=(P/'armbian/camera/kamoso-launch.py').read_bytes();compile(data,'kamoso-launch.py','exec')
code='''import base64,hashlib,json,os,pwd,subprocess
from pathlib import Path
u=pwd.getpwnam('f8test')
p=Path('/usr/local/bin/f8-kamoso');assert not p.exists()
data=base64.b64decode(PAYLOAD);compile(data,str(p),'exec');p.write_bytes(data);p.chmod(0o755)
config=Path('/home/f8test/.config/kamosorc')
assert not config.exists(),'Do not overwrite existing camera preferences'
config.write_text('[WebcamSettings]\\ndeviceObjectId=/dev/video22\\nmirrored=false\\n')
config.chmod(0o644);os.chown(config,u.pw_uid,u.pw_gid)
desktop=Path('/home/f8test/Desktop/f8-kamoso.desktop');assert not desktop.exists()
desktop.write_text('[Desktop Entry]\\nType=Application\\nName=Kamoso Photo and Video\\nName[zh_CN]=照相与录像（Kamoso）\\nExec=/usr/local/bin/f8-kamoso\\nIcon=kamoso\\nTerminal=false\\nCategories=AudioVideo;Video;\\n')
desktop.chmod(0o755);os.chown(desktop,u.pw_uid,u.pw_gid)
menu=Path('/usr/share/applications/f8-kamoso.desktop');assert not menu.exists();menu.write_bytes(desktop.read_bytes());menu.chmod(0o644)
r=subprocess.run(['desktop-file-validate',str(menu)],capture_output=True,text=True,timeout=8);assert r.returncode==0,r.stderr
print(json.dumps({'launcher_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'desktop':str(desktop),
 'camera_selection':'/dev/video22','autostart':False,'stock_kamoso_binary_modified':False},indent=2))
'''.replace('PAYLOAD',repr(base64.b64encode(data).decode()))
runner=P/'local/hardware/camera-kamoso-launcher-install01-runner.sh';assert not runner.exists()
runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=90)
assert r.returncode==0,r.stderr
(P/'local/hardware/camera-kamoso-launcher-install01.json').write_text(r.stdout);print(r.stdout)
