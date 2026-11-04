import json,os
from pathlib import Path
assert os.geteuid()==0
p=Path('/var/lib/f8-pro/touch-diagnostic/capture-r1.json');out={'kernel':json.loads(p.read_text()) if p.exists() else None}
p=Path('/home/likimk/.cache/f8-multitouch-test/results.json');out['application']=json.loads(p.read_text()) if p.exists() else None
print(json.dumps(out,indent=2))
