#!/bin/sh
set -eu
python3 -I - <<'PY'
import hashlib,json,subprocess
from pathlib import Path
out={'files':{},'iio':[]}
for n in ['/usr/local/lib/f8-pro/sensor-monitor.py','/usr/local/lib/f8-pro/compass-view.py','/etc/udev/rules.d/99-f8-pro-sensor-mount.rules']:
 p=Path(n);out['files'][n]=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
for p in Path('/sys/bus/iio/devices').glob('iio:device*'):
 name=(p/'name').read_text().strip();entry={'path':str(p),'name':name,'channels':{}}
 if name not in ['mpu6500','ak8963']:continue
 for f in p.glob('in_*'):
  if f.is_file() and any(f.name.endswith(s) for s in ['_raw','_scale','_offset','_matrix']):
   try:entry['channels'][f.name]=f.read_text().strip()
   except OSError as e:entry['channels'][f.name]=str(e)
 out['iio'].append(entry)
out['viewer_processes']=subprocess.run(['pgrep','-af','sensor-monitor.py'],capture_output=True,text=True).stdout
out['compass_calibration_present']=(Path.home()/'.config/f8-pro/compass-calibration.json').is_file()
print(json.dumps(out,indent=2))
PY
