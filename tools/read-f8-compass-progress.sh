#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,math
from pathlib import Path
status=Path('/run/user/1601/f8-compass-status.json')
config=Path('/home/f8test/.config/f8-pro/compass-calibration.json')
result={'app_status':json.loads(status.read_text()) if status.exists() else None,
        'calibration':json.loads(config.read_text()) if config.exists() else None}
for p in Path('/sys/bus/iio/devices').glob('iio:device*'):
    if (p/'name').read_text().strip()=='mpu6500':
        a=[int((p/f'in_accel_{axis}_raw').read_text()) for axis in 'xyz'];n=math.sqrt(sum(v*v for v in a))
        result['accel_raw']=a;result['z_alignment']=a[2]/n if n else None
print(json.dumps(result,ensure_ascii=False,indent=2))
PY
