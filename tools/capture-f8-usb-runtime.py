import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--sample',required=True);a=p.parse_args()
assert a.sample.isalnum()
P=Path(__file__).resolve().parents[1]
dest=P/'local/hardware/armbian-native-usb-20261101';dest.mkdir(exist_ok=True)
out=dest/(a.sample+'.json');assert not out.exists(),'Preserve evidence'
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(P/'tools/read-f8-usb-runtime.sh'),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1500:]
d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps(d,indent=2))
