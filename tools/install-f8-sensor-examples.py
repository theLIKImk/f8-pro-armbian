import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
files={n:(P/'armbian/motion'/n).read_bytes() for n in ['motion_examples_math.py','sensor_examples.py','sensor-monitor.py']}
for n,d in files.items():compile(d,n,'exec')
payload={n:{'data':base64.b64encode(d).decode(),'hash':hashlib.sha256(d).hexdigest()} for n,d in files.items()}
code='''import base64,hashlib,json
from pathlib import Path
root=Path('/usr/local/lib/f8-pro');monitor=root/'sensor-monitor.py'
assert hashlib.sha256(monitor.read_bytes()).hexdigest()=='8b924bd4b3bbdb3c33fe83275fe23cde19a042779bd624ccfbc4ba13862fb62e'
files=PAYLOAD
for n in files:
 if n!='sensor-monitor.py':assert not (root/n).exists(),n
backup=root/'sensor-monitor-before-examples.py';assert not backup.exists();backup.write_bytes(monitor.read_bytes());backup.chmod(0o755)
for n,v in files.items():
 d=base64.b64decode(v['data']);assert hashlib.sha256(d).hexdigest()==v['hash'];compile(d,n,'exec');p=root/n;temp=p.with_suffix('.new');assert not temp.exists();temp.write_bytes(d);temp.chmod(0o755);temp.replace(p)
print(json.dumps({'files':{str(root/n):v['hash'] for n,v in files.items()},'boot_changed':False,'calibration_files_changed':False},indent=2))
'''.replace('PAYLOAD',repr(payload))
runner=P/'local/hardware/sensor-examples-install01-runner.sh';assert not runner.exists();runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=90);assert r.returncode==0,r.stdout+r.stderr
(P/'local/hardware/sensor-examples-install01.json').write_text(r.stdout);print(r.stdout)
