"""Use the actual official-image module; bind/read first, enable only on success."""
import argparse,base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'local/hardware/compass-c1';out.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--attempt',choices=['01','02'],default='01');attempt=parser.parse_args().attempt
assert not (out/f'install{attempt}.json').exists()
stock=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs/usr/lib/modules/6.1.115-vendor-rk35xx/kernel/drivers/iio/magnetometer/ak8975_magn.ko')
assert hashlib.sha256(stock.read_bytes()).hexdigest()=='b97278dbecb43085d54c9e811a4af1105caf556fb9d722585a21671d79b22d31'
assets=P/'armbian/motion/official-6.1.115-compass';assets.mkdir(exist_ok=True)
(assets/stock.name).write_bytes(stock.read_bytes())
files={'/usr/libexec/f8-pro/compass/ak8975_magn.ko':(stock,0o644),
 '/usr/libexec/f8-pro/compass-start.py':(P/'armbian/motion/compass-start.py',0o755),
 '/etc/systemd/system/f8-compass.service':(P/'armbian/motion/f8-compass.service',0o644)}
payload={name:{'data':base64.b64encode(p.read_bytes()).decode(),'mode':mode,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for name,(p,mode) in files.items()}
code='''import base64,hashlib,json,subprocess,time
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='62ae5abd-745b-4b3a-85f4-5910371868b0'
assert not Path('/sys/bus/i2c/devices/3-000f').exists()
payload=PAYLOAD
for name in payload:assert not Path(name).exists() and not Path(name).is_symlink(),name
def run(args,check=True):
 p=subprocess.run(args,capture_output=True,text=True,timeout=25);r={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 if check and p.returncode:raise RuntimeError(str(r))
 return r
created=[];result={}
try:
 for name,v in payload.items():
  p=Path(name);p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(base64.b64decode(v['data']));p.chmod(v['mode']);created.append(p)
  assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
 run(['systemd-analyze','verify','/etc/systemd/system/f8-compass.service'])
 run(['systemctl','daemon-reload']);result['startup']=run(['systemctl','start','f8-compass.service'])
 devices=[p for p in Path('/sys/bus/iio/devices').glob('iio:device*') if (p/'name').read_text().strip()=='AK8963']
 assert len(devices)==1,[str(p) for p in devices];device=devices[0]
 samples=[];result['samples']=samples
 for _ in range(12):
  sample={}
  for axis in 'xyz':
   try:sample[axis]=int((device/f'in_magn_{axis}_raw').read_text())
   except OSError as e:sample[axis]={'error':str(e)}
  samples.append(sample);time.sleep(.12)
 scales={axis:(device/f'in_magn_{axis}_scale').read_text().strip() for axis in 'xyz'}
 valid=[s for s in samples if all(isinstance(v,int) for v in s.values())]
 assert len(valid)>=3,('Fewer than three complete valid samples',len(valid))
 assert any(any(v!=0 for v in s.values()) for s in valid),'All magnetic samples zero'
 result['enable']=run(['systemctl','enable','f8-compass.service'])
 result.update(success=True,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),device=str(device),samples=samples,scales_gauss_per_count=scales,
  mount_matrix=(device/'in_mount_matrix').read_text().strip() if (device/'in_mount_matrix').exists() else None,
  files={k:v['sha256'] for k,v in payload.items()},failed=run(['systemctl','--failed','--no-legend','--no-pager']),
  services=run(['systemctl','is-active','f8-compass','f8-motion','iio-sensor-proxy','f8-usb-otg','f8-bluetooth','sddm']),calibrated=False)
except Exception as e:
 result.update(success=False,error=str(e),kernel_log=run(['sh','-c','dmesg | tail -45'],False))
 run(['systemctl','stop','f8-compass.service'],False);run(['systemctl','disable','f8-compass.service'],False)
 if Path('/sys/bus/i2c/devices/3-000f').exists():Path('/sys/bus/i2c/devices/i2c-3/delete_device').write_text('0x0f\\n')
 for p in reversed(created):p.unlink(missing_ok=True)
 run(['systemctl','daemon-reload'],False)
print(json.dumps(result,indent=2))
'''.replace('PAYLOAD',repr(payload))
runner=out/f'install{attempt}-runner.sh';assert not runner.exists();runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-2000:]
d=json.loads(r.stdout);(out/f'install{attempt}.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
