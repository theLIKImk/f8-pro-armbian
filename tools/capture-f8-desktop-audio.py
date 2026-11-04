import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];dest=P/'local/hardware/armbian-native-desktop-audio-20261101';dest.mkdir(exist_ok=True)
out=dest/'before01.json';assert not out.exists()
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(P/'tools/read-f8-desktop-audio.sh'),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1500:]
d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({k:d[k] for k in ['controls','card_info','default_sink','ucm_verbs','ucm_lookup','ucm_dirs']},indent=2))
