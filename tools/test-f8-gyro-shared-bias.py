from pathlib import Path
import tempfile,json,os,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'armbian/motion'))
from gyro_stabilizer import save_shared_bias,load_shared_bias
if not Path('/proc/sys/kernel/random/boot_id').exists():raise SystemExit('Linux-only shared runtime calibration test')
previous=os.environ.get('XDG_RUNTIME_DIR')
try:
 with tempfile.TemporaryDirectory(prefix='f8-gyro-bias-test-') as tmp:
  os.environ['XDG_RUNTIME_DIR']=tmp;save_shared_bias([.01,-.02,.005]);assert load_shared_bias()==[.01,-.02,.005]
  p=Path(tmp)/'f8-gyro-bias.json';assert p.stat().st_mode&0o777==0o600
  d=json.loads(p.read_text());d['boot_id']='old-boot';p.write_text(json.dumps(d));assert load_shared_bias() is None
  d['boot_id']=Path('/proc/sys/kernel/random/boot_id').read_text().strip();d['bias_rad_s']=[999,0,0];p.write_text(json.dumps(d));assert load_shared_bias() is None
finally:
 if previous is None:os.environ.pop('XDG_RUNTIME_DIR',None)
 else:os.environ['XDG_RUNTIME_DIR']=previous
print('PASS: session bias roundtrip, 0600 mode, stale boot and invalid value rejection')
