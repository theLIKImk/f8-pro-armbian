"""Stage Bluetooth assets and enable guarded startup; do not start hardware."""
import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'local/hardware/bluetooth-bt1';out.mkdir(exist_ok=True)
assert not (out/'install01.json').exists()
assets=Path('/var/tmp/f8-pro-armbian/wireless-assets')
files={
 '/usr/libexec/f8-pro/brcm_patchram_plus1':(assets/'usr/libexec/f8-pro/brcm_patchram_plus1',0o755),
 '/usr/lib/firmware/f8-pro/BCM4362A2.hcd':(assets/'vendor/etc/firmware/BCM4362A2.hcd',0o644),
 '/usr/libexec/f8-pro/bluetooth-start.py':(P/'armbian/bluetooth/bluetooth-start.py',0o755),
 '/etc/systemd/system/f8-bluetooth.service':(P/'armbian/bluetooth/f8-bluetooth.service',0o644)}
expected={'/usr/libexec/f8-pro/brcm_patchram_plus1':'f69ba38d29d7745e88df7cfec6314a1704929dfbaf029fdd8f9c4f140e907d03',
 '/usr/lib/firmware/f8-pro/BCM4362A2.hcd':'18901a5bef1d418b6895e92d0afae36234f4160b237465dfca3d75e9844e93ef'}
payload={}
for name,(source,mode) in files.items():
    data=source.read_bytes();digest=hashlib.sha256(data).hexdigest()
    if name in expected:assert digest==expected[name]
    payload[name]={'data':base64.b64encode(data).decode(),'mode':mode,'sha256':digest}
code='''import base64,hashlib,json,subprocess
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='a56f9a1a-ca82-4f4d-96d3-fbf4df432102'
assert not Path('/dev/ttyS9').exists(),'Reassess before writing on a different boot profile'
payload=PAYLOAD
for name in payload:assert not Path(name).exists() and not Path(name).is_symlink(),name
created=[]
try:
 for name,v in payload.items():
  p=Path(name);p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(base64.b64decode(v['data']));p.chmod(v['mode']);created.append(p)
  assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
 loader=subprocess.run(['/lib/ld-linux-aarch64.so.1','--list','/usr/libexec/f8-pro/brcm_patchram_plus1'],capture_output=True,text=True,timeout=10)
 assert loader.returncode==0,loader.stderr
 subprocess.run(['systemctl','daemon-reload'],check=True,timeout=15)
 subprocess.run(['systemctl','enable','f8-bluetooth.service'],check=True,timeout=15)
 print(json.dumps({'success':True,'hardware_started':False,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
  'loader':loader.stdout,'files':{k:v['sha256'] for k,v in payload.items()}},indent=2))
except Exception:
 subprocess.run(['systemctl','disable','f8-bluetooth.service'],capture_output=True,timeout=10)
 for p in reversed(created):p.unlink()
 subprocess.run(['systemctl','daemon-reload'],timeout=15)
 raise
'''.replace('PAYLOAD',repr(payload))
runner=out/'install01-runner.sh';assert not runner.exists()
runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-2000:]
d=json.loads(r.stdout);(out/'install01.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
