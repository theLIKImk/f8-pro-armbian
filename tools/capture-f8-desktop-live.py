import json
from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1]
out=P/'local/hardware/armbian-desktop-t1-live-20261030-01/live-desktop-check.json'
assert not out.exists()
r=subprocess.run(['python3',str(P/'tools/ssh-f8-live.py'),'--address','192.168.1.227',
 '--script',str(P/'tools/read-f8-desktop-live.sh'),'--sudo'],capture_output=True,text=True,timeout=75)
assert r.returncode==0,r.stderr[-1200:]
data=json.loads(r.stdout);out.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'session':data['session'],'processes':data['user_process_names']['stdout'],
 'keyboard':data['virtual_keyboard']['stdout'],'partition_layout':data['parts'],'zstd_available':data['zstd_available'],
 'kwin_support_excerpt':data['kwin_support']['stdout'][-6500:]},indent=2))
