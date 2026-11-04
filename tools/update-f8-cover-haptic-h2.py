import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'outputs/armbian/f8-cover-haptic-h2';report=json.loads((out/'module-check.json').read_text())
data=(out/'f8-cover-haptic.ko').read_bytes();assert report['all_import_crcs_verified'] and hashlib.sha256(data).hexdigest()==report['module_sha256']=='a33e43d75e77ca997527608b2f97ab1971ae04bf7127be3d123e7172a05fcc4c'
helper=Path('/var/tmp/f8-vibrate').read_bytes();assert helper[:6]==b'\x7fELF\x02\x01' and helper[18:20]==b'\xb7\x00'
payload={'module':base64.b64encode(data).decode(),'helper':base64.b64encode(helper).decode(),'helper_hash':hashlib.sha256(helper).hexdigest()}
code='''import base64,hashlib,json,subprocess
from pathlib import Path
v=PAYLOAD
assert not Path('/sys/module/f8_cover_haptic').exists()
p=Path('/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8-cover-haptic.ko');assert hashlib.sha256(p.read_bytes()).hexdigest()=='48d45066a3c45c19ee4c1ff668325170c799c68aa2f4a6e5e5853b22cb1a27c9'
data=base64.b64decode(v['module']);assert hashlib.sha256(data).hexdigest()=='a33e43d75e77ca997527608b2f97ab1971ae04bf7127be3d123e7172a05fcc4c';p.write_bytes(data)
h=Path('/usr/local/bin/f8-vibrate');assert not h.exists();raw=base64.b64decode(v['helper']);assert hashlib.sha256(raw).hexdigest()==v['helper_hash'];h.write_bytes(raw);h.chmod(0o755)
subprocess.run(['depmod','-a'],check=True,timeout=20);subprocess.run(['modprobe','f8-cover-haptic'],check=True,timeout=10);subprocess.run(['udevadm','settle','--timeout=8'],check=True,timeout=10)
r=Path('/sys/devices/platform/f8-cover-haptic')
print(json.dumps({'module_sha256':hashlib.sha256(data).hexdigest(),'helper_sha256':v['helper_hash'],'hall_raw':(r/'hall_raw').read_text().strip(),'motor_active':(r/'motor_active').read_text().strip(),'automatic_load':False},indent=2))
'''.replace('PAYLOAD',repr(payload))
runner=P/'local/hardware/hall-haptic-update02-runner.sh';assert not runner.exists();runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=90);assert r.returncode==0,r.stdout+r.stderr
(P/'local/hardware/hall-haptic-install02.json').write_text(r.stdout);print(r.stdout)
