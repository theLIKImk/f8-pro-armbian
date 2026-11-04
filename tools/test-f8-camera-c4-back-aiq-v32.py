"""A bounded, isolated library-version comparison; no service/global install."""
import subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
base=(P/'tools/test-f8-camera-c4-back-aiq.sh').read_text()
base=base.replace("lib=C.CDLL('/opt/f8-pro-camera/aiq-v6-c4/lib/librkaiq.so')",
                  "lib=C.CDLL('/opt/f8-pro-camera/aiq-v32-c4/lib/librkaiq.so')")
base=base.replace("back-aiq-trial.log","back-aiq-v32-trial.log").replace('back-aiq02-640x480.nv12','back-aiq03-640x480.nv12')
anchor="root=Path('/opt/f8-pro-camera/aiq-v6-c4');folder=Path('/run/f8-camera-c4')\n"
assert base.count(anchor)==1
install='''import hashlib
newlib=Path('/opt/f8-pro-camera/aiq-v32-c4/lib/librkaiq.so');assert not newlib.exists()
data=Path('/home/f8test/.cache/f8-camera-aiq-c4-stage/librkaiq-v32.so').read_bytes()
assert hashlib.sha256(data).hexdigest()=='1b34d9d85c2eee9bf49ee82147fb054c47c8a9dadddd480ccf07f96dda2db765'
newlib.parent.mkdir(parents=True,exist_ok=True);newlib.write_bytes(data);newlib.chmod(0o644)
dep=subprocess.run(['ldd',str(newlib)],capture_output=True,text=True,timeout=8)
assert dep.returncode==0 and 'not found' not in dep.stdout+dep.stderr,(dep.stdout,dep.stderr)
'''
base=base.replace(anchor,anchor+install)
runner=P/'local/hardware/camera-c4-back-aiq-v32-runner.sh';assert not runner.exists()
runner.write_text(base)
result=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=90)
assert result.returncode==0,result.stderr
(P/'local/hardware/camera-c4-back-aiq-v32-test01.json').write_text(result.stdout)
print('Saved camera-c4-back-aiq-v32-test01.json')
