import argparse,json,subprocess
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--revision',choices=['u3','u4r1'],default='u3');args=parser.parse_args()
P=Path(__file__).resolve().parents[1];dest=P/('local/hardware/armbian-native-usb-20261101/'+args.revision);out=dest/'phy-host01.json';assert not out.exists()
script=P/'tools/test-f8-u3-phy-host.sh'
if args.revision=='u4r1':
    boot=json.loads((dest/'identity.json').read_text())['boot_id']
    text=script.read_text().replace('a262ec8f-29d5-4110-a7f0-f82dc0034611',boot).replace('usb-u3-phy-host01','usb-u4r1-phy-host01')
    script=dest/'phy-host01-runner.sh';assert not script.exists();script.write_text(text)
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(script),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1500:]
d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
