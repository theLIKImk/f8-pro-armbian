import os,json,subprocess,hashlib
from pathlib import Path
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=12);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
o={'modules':run(['modinfo','ls_em30918']),'drivers':[p.name for p in Path('/sys/bus/i2c/drivers').iterdir() if any(x in p.name for x in ['em30','sensor','mpu','ak89'])],'module_files':[str(p) for p in Path('/usr/lib/modules/'+os.uname().release).rglob('*') if p.is_file() and any(x in p.name.lower() for x in ['em309','sensor-dev'])],'files':{},'calibration':None,'i2c_dev':Path('/dev/i2c-3').exists()}
for name in ['sensor-monitor.py','sensor_examples.py','motion_examples_math.py','compass-view.py']:
 p=Path('/usr/local/lib/f8-pro')/name;o['files'][name]=hashlib.sha256(p.read_bytes()).hexdigest()
p=Path('/home/likimk/.config/f8-pro/compass-calibration.json')
if p.exists():
 c=json.loads(p.read_text());o['calibration']={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'version':c.get('version'),'method':c.get('method'),'sample_count':c.get('sample_count')}
print(json.dumps(o))
