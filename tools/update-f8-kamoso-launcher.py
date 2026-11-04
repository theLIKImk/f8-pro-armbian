import base64,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
data=(P/'armbian/camera/kamoso-launch.py').read_bytes();compile(data,'launcher','exec')
code='''import base64,hashlib,json
from pathlib import Path
p=Path('/usr/local/bin/f8-kamoso')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='8240526bc3ac2f2e393dd69e3d1e01d569e0dfdd2af05d891e3e0465fc0928a2'
data=base64.b64decode(PAYLOAD);compile(data,str(p),'exec')
p.write_bytes(data);p.chmod(0o755)
print(json.dumps({'sha256':hashlib.sha256(data).hexdigest()}))
'''.replace('PAYLOAD',repr(base64.b64encode(data).decode()))
runner=P/'local/hardware/camera-kamoso-update02-runner.sh';assert not runner.exists()
runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=90)
assert r.returncode==0,r.stderr
(P/'local/hardware/camera-kamoso-update02.json').write_text(r.stdout);print(r.stdout)
