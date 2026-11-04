import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
out=P/'local/hardware/armbian-native-audio-a1-20261030-01/softtone-02.json';assert not out.exists()
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(P/'tools/test-f8-audio-a1-softtone.sh'),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1300:]
d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({k:d.get(k) for k in ['boot_id','duration_seconds','output_gain','output_route','play','restore','sound_log']},indent=2))
