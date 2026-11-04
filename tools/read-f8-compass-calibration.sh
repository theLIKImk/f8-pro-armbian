#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,math,time
from pathlib import Path
f=Path('/home/f8test/.config/f8-pro/compass-calibration.json')
cal=json.loads(f.read_text()) if f.exists() else None
devices=[p for p in Path('/sys/bus/iio/devices').glob('iio:device*') if (p/'name').read_text().strip().lower()=='ak8963']
assert len(devices)==1
samples=[]
for _ in range(8):
    try:
        v=[int((devices[0]/f'in_magn_{a}_raw').read_text())*float((devices[0]/f'in_magn_{a}_scale').read_text())*100 for a in 'xyz']
        s={'ut':v}
        if cal:
            corrected=[(v[i]-cal['offset_ut'][i])*cal['scale'][i] for i in range(3)]
            s.update(corrected_ut=corrected,old_heading=math.degrees(math.atan2(-corrected[1],corrected[0]))%360)
        samples.append(s)
    except OSError as e:samples.append({'error':str(e)})
    time.sleep(.15)
print(json.dumps({'calibration':cal,'samples':samples},indent=2))
PY
