import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'outputs/armbian/f8-cover-haptic-h1';report=json.loads((out/'module-check.json').read_text());data=(out/'f8-cover-haptic.ko').read_bytes()
assert report['all_import_crcs_verified'] and hashlib.sha256(data).hexdigest()==report['module_sha256']=='48d45066a3c45c19ee4c1ff668325170c799c68aa2f4a6e5e5853b22cb1a27c9'
code='''import base64,hashlib,json,subprocess
from pathlib import Path
assert subprocess.check_output(['uname','-r'],text=True).strip()=='6.1.115-vendor-rk35xx'
assert Path('/proc/device-tree/model').read_bytes().startswith(b'F8-PRO')
assert not Path('/sys/module/f8_cover_haptic').exists()
pins='\\n'.join(p.read_text() for p in Path('/sys/kernel/debug/pinctrl').glob('*/pinmux-pins'))
for number in [27,114]:
 lines=[s for s in pins.splitlines() if s.startswith('pin '+str(number)+' ')];assert len(lines)==1 and '(MUX UNCLAIMED) (GPIO UNCLAIMED)' in lines[0],lines
gpio=Path('/sys/kernel/debug/gpio').read_text();assert 'gpio-27 ' not in gpio and 'gpio-114 ' not in gpio
p=Path('/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8-cover-haptic.ko');assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True)
data=base64.b64decode(DATA);assert hashlib.sha256(data).hexdigest()=='48d45066a3c45c19ee4c1ff668325170c799c68aa2f4a6e5e5853b22cb1a27c9';p.write_bytes(data);p.chmod(0o644)
rule=Path('/etc/udev/rules.d/99-f8-cover-haptic.rules');assert not rule.exists()
rule.write_text('SUBSYSTEM=="input", KERNEL=="event*", ATTRS{name}=="F8 Hall Cover", TAG+="seat", TAG+="uaccess", SYMLINK+="input/f8-cover"\\nSUBSYSTEM=="input", KERNEL=="event*", ATTRS{name}=="F8 Haptic Motor", TAG+="seat", TAG+="uaccess", SYMLINK+="input/f8-haptic"\\n')
subprocess.run(['udevadm','control','--reload-rules'],check=True,timeout=8)
subprocess.run(['depmod','-a'],check=True,timeout=20);subprocess.run(['modprobe','f8-cover-haptic'],check=True,timeout=10);subprocess.run(['udevadm','settle','--timeout=8'],check=True,timeout=10)
root=Path('/sys/devices/platform/f8-cover-haptic')
print(json.dumps({'module':str(p),'sha256':hashlib.sha256(data).hexdigest(),'hall_raw':(root/'hall_raw').read_text().strip(),'motor_active':(root/'motor_active').read_text().strip(),'persistent_load':False},indent=2))
'''.replace('DATA',repr(base64.b64encode(data).decode()))
runner=P/'local/hardware/hall-haptic-install01-runner.sh';assert not runner.exists();runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=90);assert r.returncode==0,r.stdout+r.stderr
(P/'local/hardware/hall-haptic-install01.json').write_text(r.stdout);print(r.stdout)
