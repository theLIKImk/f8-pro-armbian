import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
expected={'sensor_examples.py':'659d63ce35a5597c0bdc498759ee532a27fd8053a65d45290d25733ccf3161c2'}
files={n:(P/'armbian/motion'/n).read_bytes() for n in expected}
for n,d in files.items():compile(d,n,'exec')
payload={n:{'data':base64.b64encode(d).decode(),'expected':expected[n]} for n,d in files.items()}
code='''import base64,hashlib,json
from pathlib import Path
root=Path('/usr/local/lib/f8-pro');files=PAYLOAD
for n,v in files.items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==v['expected']
for n,v in files.items():
 d=base64.b64decode(v['data']);compile(d,n,'exec');p=root/n;temp=p.with_suffix('.new');assert not temp.exists();temp.write_bytes(d);temp.chmod(0o755);temp.replace(p)
print(json.dumps({n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in files},indent=2))
'''.replace('PAYLOAD',repr(payload))
runner=P/'local/hardware/sensor-examples-update03-runner.sh';assert not runner.exists();runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=90);assert r.returncode==0,r.stdout+r.stderr
(P/'local/hardware/sensor-examples-update03.json').write_text(r.stdout);print(r.stdout)
