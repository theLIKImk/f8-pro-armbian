"""Bounded SSH reconnection check after the authorized tablet restart."""
import json,subprocess,time
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'local/hardware/armbian-native-usb-20261101/u5/reboot-verification01.json';assert not out.exists()
deadline=time.monotonic()+150;attempt=0;last=''
while time.monotonic()<deadline:
    attempt+=1
    r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(P/'tools/verify-f8-u5-usb-reboot.sh'),'--sudo'],capture_output=True,text=True,timeout=100)
    if r.returncode==0:
        d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2),flush=True);break
    last=r.stderr[-1600:];print('Waiting for fresh boot and automatic USB startup; attempt '+str(attempt),flush=True)
    time.sleep(3)
else:
    out.with_suffix('.failure.txt').write_text(last);raise RuntimeError(last)
