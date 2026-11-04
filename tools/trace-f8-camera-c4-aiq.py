"""Bounded ioctl/thread trace of the isolated back-camera AIQ trial."""
import subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'tools/test-f8-camera-c4-back-aiq.sh').read_text()
s=s.replace('back-aiq-trial.log','back-aiq-trace01.log').replace('back-aiq02-640x480.nv12','back-aiq-trace01-640x480.nv12')
s=s.replace("['python3','-u','-c',child]","['strace','-f','-tt','-T','-yy','-s','128','-e','trace=ioctl,clone,clone3,sched_setscheduler,openat,poll,ppoll','-o','/run/f8-camera-c4/back-aiq-trace01.txt','python3','-u','-c',child]")
r=P/'local/hardware/camera-c4-back-aiq-trace01-runner.sh';assert not r.exists();r.write_text(s)
p=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(r),'--sudo'],capture_output=True,text=True,timeout=90)
assert p.returncode==0,p.stderr
(P/'local/hardware/camera-c4-back-aiq-trace01.json').write_text(p.stdout)
print('Saved trace trial result')
