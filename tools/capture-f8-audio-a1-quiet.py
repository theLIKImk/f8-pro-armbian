import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
out=P/'local/hardware/armbian-native-audio-a1-20261030-01/quiet-gpio-01.json';assert not out.exists()
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(P/'tools/quiet-f8-audio-and-read-gpios.sh'),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1000:]
d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({k:v for k,v in d.items() if k!='before'},indent=2))
