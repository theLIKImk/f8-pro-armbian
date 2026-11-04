import base64,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'outputs/armbian/f8-flash-f1'
report=json.loads((out/'module-check.json').read_text());data=(out/'f8-flash.ko').read_bytes()
assert report['all_import_crcs_verified'] and hashlib.sha256(data).hexdigest()==report['module_sha256']
code='''import base64,hashlib,json,os,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert os.uname().release=='6.1.115-vendor-rk35xx'
assert Path('/proc/device-tree/model').read_bytes().startswith(b'F8-PRO')
assert not Path('/sys/module/f8_flash').exists()
pins='\\n'.join(p.read_text() for p in Path('/sys/kernel/debug/pinctrl').glob('*/pinmux-pins'))
lines=[l for l in pins.splitlines() if l.startswith('pin 113 ')]
assert len(lines)==1 and '(MUX UNCLAIMED) (GPIO UNCLAIMED)' in lines[0],lines
assert 'gpio-113 ' not in Path('/sys/kernel/debug/gpio').read_text()
data=base64.b64decode(MODULE_DATA);expected=MODULE_SHA
assert hashlib.sha256(data).hexdigest()==expected
p=Path('/usr/local/lib/f8-pro/experimental/f8-flash-f1.ko');p.parent.mkdir(parents=True,exist_ok=True)
assert not p.is_symlink()
if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
else:p.write_bytes(data);p.chmod(0o644)
subprocess.run(['insmod',str(p)],check=True,timeout=10)
led=Path('/sys/class/leds/f8:white:flash');assert led.exists()
assert str(led.resolve()).startswith('/sys/devices/platform/f8-flash/')
b=led/'brightness';assert b.read_text().strip()=='0'
assert (led/'max_brightness').read_text().strip()=='1'
samples=[];start=time.monotonic()
try:
 b.write_text('1\\n')
 for _ in range(9):
  samples.append({'elapsed':round(time.monotonic()-start,3),'brightness':int(b.read_text())})
  time.sleep(.1)
finally:b.write_text('0\\n')
assert any(s['brightness']==1 for s in samples[:3]),samples
assert all(s['brightness']==0 for s in samples if s['elapsed']>=.7),samples
gpio=Path('/sys/kernel/debug/gpio').read_text()
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'module_sha256':expected,'led':str(led),'samples':samples,'final_brightness':b.read_text().strip(),'gpio113':[l for l in gpio.splitlines() if 'gpio-113 ' in l],'gpio114_motor':[l for l in gpio.splitlines() if 'gpio-114 ' in l],'persistent_load':False,'boot_changed':False},indent=2))
'''.replace('MODULE_DATA',repr(base64.b64encode(data).decode())).replace('MODULE_SHA',repr(report['module_sha256']))
compile(code,'flash-runner','exec')
runner=P/'local/hardware/flash-f1-test-runner.py';runner.write_text(code)
print(runner)
