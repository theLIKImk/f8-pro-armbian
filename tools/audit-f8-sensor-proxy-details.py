import json,subprocess,re
from pathlib import Path
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
o={'proxy_introspection':run(['busctl','--system','introspect','net.hadess.SensorProxy','/net/hadess/SensorProxy']),'compass':run(['busctl','--system','get-property','net.hadess.SensorProxy','/net/hadess/SensorProxy','net.hadess.SensorProxy.Compass','HasCompass']),'dt':{}}
base=Path('/sys/firmware/devicetree/base')
for p in base.rglob('*'):
 if not p.is_dir():continue
 c=p/'compatible';compatible=c.read_bytes() if c.is_file() else b''
 if re.search(r'mpu|gyro|compass|ak896|em309|mma7660|light@|proximity|hall|pressure|acceler|imu@',p.name+' '+compatible.decode(errors='replace'),re.I):
  o['dt'][str(p.relative_to(base))]={f.name:f.read_bytes().hex() for f in p.iterdir() if f.is_file() and f.name in ['compatible','reg','status','layout','poll_delay_ms','interrupts','mount-matrix']}
print(json.dumps(o))
