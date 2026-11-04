"""Capture authenticated SSH evidence privately; never print credentials."""
import datetime
import json
from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1]
out=P/'local/hardware/armbian-official-g6-r5-20261030-01';out.mkdir(exist_ok=True)
file=out/'ssh-before-charger.json';assert not file.exists(),'Preserve baseline'
result=subprocess.run(['python3',str(P/'tools/ssh-f8-live.py'),'--address','192.168.1.227',
 '--script',str(P/'tools/read-f8-live-baseline.sh'),'--sudo'],capture_output=True,text=True,timeout=90)
assert result.returncode==0,result.stderr[-1200:]
data=json.loads(result.stdout);data['collector_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
file.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'authenticated':True,'kernel':data['uname'],'power_age_seconds':data['power_age_seconds'],
 'gpu_accepted':data['gpu']['hardware_accepted'] if data['gpu'] else None,
 'cw':data['power']['devices']['0x62']['decoded'],'bq':data['power']['devices']['0x6a']['decoded'],
 'units':data['units']['stdout']},indent=2))
