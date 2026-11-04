"""Save charger-connected passive snapshots and compare to immutable pre-swap baseline."""
import datetime
import json
from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1]
out=P/'local/hardware/armbian-official-g6-r5-20261030-01'
file=out/'ssh-after-charger-01.json';assert not file.exists(),'Do not overwrite observations'
before=json.loads((out/'ssh-before-charger.json').read_text())
r=subprocess.run(['python3',str(P/'tools/ssh-f8-live.py'),'--address','192.168.1.227',
 '--script',str(P/'tools/read-f8-charger-samples.sh'),'--sudo'],capture_output=True,text=True,timeout=80)
assert r.returncode==0,r.stderr[-1500:]
data=json.loads(r.stdout);data['collector_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
data['same_boot_as_before']=data['boot_id']==before['boot_id']
file.write_text(json.dumps(data,indent=2)+'\n')
rows=[]
for sample in data['samples']:
    power=sample['power'];bq=power['devices']['0x6a'];cw=power['devices']['0x62']['decoded']
    rows.append({'uptime':sample['uptime_seconds'],'age':sample['age_seconds'],
      'cw_mv':cw['voltage_mv_reference_formula'],'soc':cw['soc_raw_percent'],'bq':bq['decoded'],
      'raw_0b':bq['raw']['0xb'],'raw_11':bq['raw']['0x11'],'raw_12':bq['raw']['0x12']})
print(json.dumps({'same_boot':data['same_boot_as_before'],
 'before_cw_mv':before['power']['devices']['0x62']['decoded']['voltage_mv_reference_formula'],
 'samples':rows,'failed_units':data['failed_units']},indent=2))
