"""Update only our preview file after verifying its previous installed hash."""
import argparse,base64,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--expected-sha256',required=True);p.add_argument('--sample',type=int,required=True);p.add_argument('--backend',action='store_true');a=p.parse_args()
assert len(a.expected_sha256)==64 and all(c in '0123456789abcdef' for c in a.expected_sha256)
P=Path(__file__).resolve().parents[1];filename='aiq-backend.py' if a.backend else 'camera-preview.py'
data=(P/'armbian/camera'/filename).read_bytes();compile(data,filename,'exec')
code='''import base64,hashlib,json
from pathlib import Path
p=Path('/usr/local/lib/f8-pro/camera-preview.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()==EXPECTED
lib=Path('/usr/local/lib/f8-pro/libf8-camera-pixels.so')
if not lib.exists():
 raw=Path('/home/f8test/.cache/f8-camera-aiq-c4-stage/libf8-camera-pixels.so').read_bytes()
 assert hashlib.sha256(raw).hexdigest()=='ef077246c1088cff2d3de8e69730430818fe2ad8c62215408e0380ba5ee7afaf'
 lib.write_bytes(raw);lib.chmod(0o644)
assert hashlib.sha256(lib.read_bytes()).hexdigest()=='ef077246c1088cff2d3de8e69730430818fe2ad8c62215408e0380ba5ee7afaf'
data=base64.b64decode(DATA);compile(data,str(p),'exec')
temp=p.with_suffix('.new');assert not temp.exists();temp.write_bytes(data);temp.chmod(0o755);temp.replace(p)
print(json.dumps({'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'started':False}))
'''.replace('EXPECTED',repr(a.expected_sha256)).replace('DATA',repr(base64.b64encode(data).decode()))
if a.backend:code=code.replace('/usr/local/lib/f8-pro/camera-preview.py','/usr/local/lib/f8-pro/aiq-backend.py')
runner=P/f'local/hardware/camera-c4-preview-update{a.sample:02d}-runner.sh';assert not runner.exists()
runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=90)
assert r.returncode==0,r.stderr
(P/f'local/hardware/camera-c4-preview-update{a.sample:02d}.json').write_text(r.stdout);print(r.stdout)
