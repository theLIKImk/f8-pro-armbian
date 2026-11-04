"""Read-only current touch-rate prerequisites; never opens the I2C device."""
import hashlib,json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
dev=Path('/sys/bus/i2c/devices/4-0040');assert dev.exists()
dt=Path('/sys/firmware/devicetree/base/i2c@feac0000')
o={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'kernel':os.uname().release,'driver':str((dev/'driver').resolve()),'module':{},'touch_interfaces':{},'nodes':{}}
for name in ['srcversion','version','taint']:
 p=Path('/sys/module/f8_gsl_shuping')/name
 if p.exists():o['module'][name]=p.read_text().strip()
for p in [dt,*[p for p in dt.iterdir() if p.is_dir()]]:
 o['nodes'][str(p.relative_to(dt))]={q.name:q.read_bytes().hex() for q in p.iterdir() if q.is_file() and q.name in ['compatible','clock-frequency','reg','status','name']}
o['device_attribute_names']=[p.name for p in dev.iterdir()]
for p in Path('/sys/module/f8_gsl_shuping/parameters').glob('*'):o['module'][p.name]=p.read_text().strip()
for p in Path('/sys/class/input').glob('event*'):
 name=p/'device/name'
 if name.exists() and name.read_text().strip()=='f8-gsl-shuping':
  o['touch_interfaces'][p.name]={'path':str(p.resolve()),'device_attributes':[q.name for q in (p/'device').iterdir()]}
o['irq']=[l for l in Path('/proc/interrupts').read_text().splitlines() if 'gsl' in l.lower()]
o['proc_interfaces']=[p.name for p in Path('/proc').iterdir() if 'gsl' in p.name.lower()]
for name in ['bb8fd9db0bf16972e6760ca9d8ba8489e91a516c31269fc770346fe75d7a505d']:
 p=Path('/usr/libexec/f8-pro/f8_gsl_shuping.ko');o['persistent_module_sha256']=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
print(json.dumps(o,indent=2))
