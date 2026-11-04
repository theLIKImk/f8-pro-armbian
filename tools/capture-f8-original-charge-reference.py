"""Run only after user confirms original BOOT restored; preserve native reference."""
import datetime
import json
from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1]
out=P/'local/hardware/armbian-official-g6-r5-20261030-01/original-charge-reference-01.json'
assert not out.exists()
r=subprocess.run(['python3',str(P/'tools/ssh-f8.py'),'--address','192.168.1.227',
 '--script',str(P/'tools/read-f8-original-charge-reference.sh'),'--sudo','--timeout','60'],
 capture_output=True,text=True,timeout=80)
assert r.returncode==0,r.stderr[-1500:]
data=json.loads(r.stdout);data['collector_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
with out.open('x') as stream:stream.write(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
