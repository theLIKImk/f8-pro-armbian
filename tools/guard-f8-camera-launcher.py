import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'local/hardware/camera-c2'
assert not (out/'launcher01.json').exists()
data=base64.b64encode((P/'armbian/camera/f8-camera-test').read_bytes()).decode()
code='''import base64,hashlib,json
from pathlib import Path
p=Path('/usr/local/bin/f8-camera-test');assert not p.exists()
p.write_bytes(base64.b64decode(PAYLOAD));p.chmod(0o755)
desktop=Path('/home/f8test/Desktop/f8-camera-test.desktop')
s=desktop.read_text();assert 'Exec=/usr/bin/qv4l2\\n' in s
desktop.write_text(s.replace('Exec=/usr/bin/qv4l2\\n','Exec=/usr/local/bin/f8-camera-test\\n'))
print(json.dumps({'launcher_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'desktop_shortcut':str(desktop),'launched':False},indent=2))
'''.replace('PAYLOAD',repr(data))
runner=out/'launcher01-runner.sh';runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100);assert r.returncode==0,r.stderr[-1500:]
d=json.loads(r.stdout);(out/'launcher01.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
