"""Stage C2 startup, disabled by profile on the running C1; do not run it."""
import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'local/hardware/camera-c2';out.mkdir(exist_ok=True)
assert not (out/'install01.json').exists()
files={'/usr/libexec/f8-pro/camera-start.py':(P/'armbian/camera/camera-start.py',0o755),
 '/etc/systemd/system/f8-camera-start.service':(P/'armbian/camera/f8-camera-start.service',0o644)}
payload={name:{'data':base64.b64encode(p.read_bytes()).decode(),'mode':mode,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for name,(p,mode) in files.items()}
code='''import base64,hashlib,json,subprocess
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='d7fc7e8b-9936-4190-9b5b-3ec1a33b0576'
assert Path('/sys/firmware/devicetree/base/chosen/f8-camera-trial').read_bytes()==b'c1\\0'
payload=PAYLOAD
for name in payload:assert not Path(name).exists() and not Path(name).is_symlink(),name
for name,v in payload.items():
 p=Path(name);p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(base64.b64decode(v['data']));p.chmod(v['mode']);assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
p=subprocess.run(['systemd-analyze','verify','/etc/systemd/system/f8-camera-start.service'],capture_output=True,text=True,timeout=15)
assert p.returncode==0,p.stderr
subprocess.run(['systemctl','daemon-reload'],check=True,timeout=15)
subprocess.run(['systemctl','enable','f8-camera-start.service'],check=True,timeout=15)
print(json.dumps({'installed':True,'started':False,'files':{k:v['sha256'] for k,v in payload.items()},'unit_verify':p.stderr},indent=2))
'''.replace('PAYLOAD',repr(payload))
runner=out/'install01-runner.sh';assert not runner.exists();runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-2000:]
d=json.loads(r.stdout);(out/'install01.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
