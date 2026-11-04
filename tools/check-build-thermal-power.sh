set -eu
python3 - <<'PY'
from pathlib import Path
import json
thermal=[]
for zone in sorted(Path('/sys/class/thermal').glob('thermal_zone*')):
    thermal.append({'zone':zone.name,'type':(zone/'type').read_text().strip(),'milli_celsius':int((zone/'temp').read_text())})
power=[]
for supply in sorted(Path('/sys/class/power_supply').glob('*')):
    item={'name':supply.name}
    for key in ['type','status','online','capacity','temp','voltage_now','current_now']:
        p=supply/key
        if p.exists():item[key]=p.read_text().strip()
    power.append(item)
print(json.dumps({'thermal':thermal,'power':power},indent=2))
work=Path('/home/alarm/f8-pro-builds/kwin-6.7.5-v73ibK4G')
print('\nKWIN LOG TAIL\n'+'\n'.join((work/'build.log').read_text(errors='replace').splitlines()[-4:]))
print('\nTHERMAL HISTORY TAIL\n'+'\n'.join((work/'thermal-history.csv').read_text().splitlines()[-3:]))
PY
