"""Trace the ordinary-user initialization failure without changing permissions."""
import subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'local/hardware/camera-c4-aiq-otp-user-long-runner.sh').read_text()
s=s.replace('back-aiq-fps14-otp-user-long.log','back-aiq-user-trace.log').replace('back-aiq-fps14-otp-user-long-640x480.nv12','back-aiq-user-trace-640x480.nv12')
s=s.replace("['python3','-u','-c',child]","['strace','-f','-tt','-e','trace=file,network','-o',str(folder/'user-init-trace.txt'),'python3','-u','-c',child]")
r=P/'local/hardware/camera-c4-user-aiq-trace-runner.sh';assert not r.exists();r.write_text(s)
p=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(r)],capture_output=True,text=True,timeout=90)
assert p.returncode==0,p.stderr
(P/'local/hardware/camera-c4-user-aiq-trace01.json').write_text(p.stdout)
print('Saved ordinary-user init trace')
