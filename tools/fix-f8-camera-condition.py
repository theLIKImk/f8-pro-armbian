import base64,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'local/hardware/camera-c2';assert not (out/'condition-fix01.json').exists()
data=base64.b64encode((P/'armbian/camera/f8-camera-start.service').read_bytes()).decode()
code='''import base64,hashlib,json,subprocess
from pathlib import Path
p=Path('/etc/systemd/system/f8-camera-start.service')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='44e621b2f4d122af614c8c50475912c75e26e801a92b78e8e99a89e95c2e189e'
p.write_bytes(base64.b64decode(PAYLOAD));p.chmod(0o644)
r=subprocess.run(['systemd-analyze','verify',str(p)],capture_output=True,text=True,timeout=15)
assert r.returncode==0 and not r.stderr,r.stderr
test=subprocess.run(['/usr/bin/grep','-q','^c2','/sys/firmware/devicetree/base/chosen/f8-camera-trial'])
assert test.returncode==1,'Current C1 should skip C2 service'
subprocess.run(['systemctl','daemon-reload'],check=True,timeout=15)
print(json.dumps({'unit_verify_clean':True,'c1_guard_skips':True,'started':False,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2))
'''.replace('PAYLOAD',repr(data))
runner=out/'condition-fix01-runner.sh';runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100);assert r.returncode==0,r.stderr[-1800:]
d=json.loads(r.stdout);(out/'condition-fix01.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
