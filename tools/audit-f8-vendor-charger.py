"""Disassemble original charger paths offline; never connect to or alter tablet."""
import json
from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1]
symbols=json.loads((P/'analysis/armbian/touch-static/all-symbols.json').read_text())
starts=sorted({x['file_offset'] for x in symbols if x['file_offset']>=0})
out=P/'analysis/armbian/live-g6/vendor-charger';out.mkdir(exist_ok=True)
rows=[]
for name in ['bq25890_power_supply_get_property','bq25890_probe','bq25890_get_chip_state']:
    symbol=next(x for x in symbols if x['name']==name)
    start=symbol['file_offset'];end=next(x for x in starts if x>start)
    result=subprocess.run(['aarch64-linux-gnu-objdump','-D','-b','binary','-m','aarch64',
       '--start-address='+str(start),'--stop-address='+str(end),
       str(P/'vendor/ubuntu-5.10.160/boot-assets/Image')],capture_output=True,text=True,check=True)
    (out/(name+'.asm')).write_text(result.stdout)
    rows.append({'name':name,'start':start,'end':end})
(out/'index.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows))
