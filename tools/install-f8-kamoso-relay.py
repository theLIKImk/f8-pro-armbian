import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
data=(P/'armbian/camera/kamoso-relay-launch.py').read_bytes();compile(data,'launcher','exec')
code='''import base64,hashlib,json
from pathlib import Path
p=Path('/usr/local/bin/f8-kamoso')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='0c2e2f1293c1dae33147231b9604fb5b65656cda81d11a683eb2d5fff26a960e'
backup=Path('/usr/local/lib/f8-pro/kamoso-direct-launch.py');assert not backup.exists();backup.write_bytes(p.read_bytes());backup.chmod(0o755)
data=base64.b64decode(DATA);compile(data,str(p),'exec');p.write_bytes(data);p.chmod(0o755)
for n in ['/usr/share/applications/f8-kamoso.desktop','/home/f8test/Desktop/f8-kamoso.desktop']:
 q=Path(n);s=q.read_text();assert 'Exec=/usr/local/bin/f8-kamoso\\n' in s
 s=s.replace('Name[zh_CN]=照相与录像（Kamoso）','Name[zh_CN]=Kamoso（兼容中继）');q.write_text(s)
print(json.dumps({'launcher_sha256':hashlib.sha256(data).hexdigest(),'physical_camera_access':False,'requires_user_enabled_relay':True}))
'''.replace('DATA',repr(base64.b64encode(data).decode()))
runner=P/'local/hardware/camera-kamoso-relay-install01-runner.sh';assert not runner.exists()
runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=90)
assert r.returncode==0,r.stderr
(P/'local/hardware/camera-kamoso-relay-install01.json').write_text(r.stdout);print(r.stdout)
