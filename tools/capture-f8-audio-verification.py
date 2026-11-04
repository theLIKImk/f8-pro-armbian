import argparse,json,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--sample',required=True);p.add_argument('--new-boot',action='store_true');a=p.parse_args();assert a.sample.isalnum()
P=Path(__file__).resolve().parents[1];out=P/('local/hardware/armbian-native-desktop-audio-20261101/'+a.sample+'.json');assert not out.exists()
deadline=time.monotonic()+(150 if a.new_boot else 1);last=''
while True:
    r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(P/'tools/verify-f8-desktop-audio.sh'),'--sudo'],capture_output=True,text=True,timeout=100)
    if r.returncode==0:
        d=json.loads(r.stdout)
        if not a.new_boot or d['boot_id']!='3f9b409e-0860-438a-a5eb-2ac768dbafd2':
            out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2),flush=True);break
    last=r.stderr[-1600:]
    if time.monotonic()>deadline:raise RuntimeError(last or 'Expected a fresh boot')
    print('Waiting for fresh desktop audio profile',flush=True);time.sleep(3)
