import json,subprocess,argparse
from pathlib import Path
P=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--resume',action='store_true');args=p.parse_args()
dest=P/'local/hardware/armbian-native-audio-a1-20261030-01';dest.mkdir(exist_ok=True)
for name,script in [('audio-runtime.json','read-f8-audio-runtime.sh'),('desktop-acceptance.json','verify-f8-native-desktop.sh')]:
    out=dest/name
    if out.exists():
        assert args.resume,'Preserve existing evidence; use --resume only for missing outputs'
        continue
    r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(P/'tools'/script),'--sudo'],capture_output=True,text=True,timeout=100)
    assert r.returncode==0,r.stderr[-1500:]
    d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n')
    if name=='audio-runtime.json':print(json.dumps(d,indent=2))
    else:print(json.dumps({'desktop_boot_id':d['boot_id'],'reboot_persistence_confirmed':d['reboot_persistence_confirmed'],'keyboard':d['keyboard']},indent=2))
