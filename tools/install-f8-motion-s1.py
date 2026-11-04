"""Stage sensor modules and guarded late-start service without touching sensor hardware."""
import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'local/hardware/motion-s1';out.mkdir(exist_ok=True)
assert not (out/'install01.json').exists()
report=json.loads((P/'armbian/motion/official-6.1.115-iio/module-check.json').read_text())
assert report['all_external_import_crcs_match_actual_26_8_1_kernel']
files={'/usr/libexec/f8-pro/motion-start.py':(P/'armbian/motion/motion-start.py',0o755),
 '/etc/systemd/system/f8-motion.service':(P/'armbian/motion/f8-motion.service',0o644)}
for m in report['modules']:
    src=P/'armbian/motion/official-6.1.115-iio'/m['file'];assert hashlib.sha256(src.read_bytes()).hexdigest()==m['sha256']
    files['/usr/libexec/f8-pro/motion/'+m['file']]=(src,0o644)
payload={name:{'data':base64.b64encode(p.read_bytes()).decode(),'mode':mode,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for name,(p,mode) in files.items()}
code='''import base64,hashlib,json,subprocess
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='5da89e9f-10f3-4d00-87bf-97df844b1100'
assert not Path('/sys/firmware/devicetree/base/chosen/f8-motion-trial').exists()
pins='\\n'.join(p.read_text() for p in Path('/sys/kernel/debug/pinctrl').glob('*/pinmux-pins'))
for pin,bank,offset in [(111,3,15),(112,3,16),(115,3,19)]:
 line=next(s for s in pins.splitlines() if s.startswith(f'pin {pin} (gpio{bank}-{offset}):'))
 assert '(MUX UNCLAIMED) (GPIO UNCLAIMED)' in line,line
payload=PAYLOAD
for name in payload:assert not Path(name).exists() and not Path(name).is_symlink(),name
created=[]
try:
 for name,v in payload.items():
  p=Path(name);p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(base64.b64decode(v['data']));p.chmod(v['mode']);created.append(p)
  assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
 verify=subprocess.run(['systemd-analyze','verify','/etc/systemd/system/f8-motion.service'],capture_output=True,text=True,timeout=15)
 assert verify.returncode==0,verify.stderr
 subprocess.run(['systemctl','daemon-reload'],check=True,timeout=15)
 subprocess.run(['systemctl','enable','f8-motion.service'],check=True,timeout=15)
 print(json.dumps({'success':True,'hardware_started':False,'pins_unclaimed_verified':True,'unit_verify':verify.stderr,
  'files':{k:v['sha256'] for k,v in payload.items()}},indent=2))
except Exception:
 subprocess.run(['systemctl','disable','f8-motion.service'],capture_output=True,timeout=10)
 for p in reversed(created):p.unlink()
 subprocess.run(['systemctl','daemon-reload'],timeout=15)
 raise
'''.replace('PAYLOAD',repr(payload))
runner=out/'install01-runner.sh';assert not runner.exists();runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-2000:]
d=json.loads(r.stdout);(out/'install01.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
