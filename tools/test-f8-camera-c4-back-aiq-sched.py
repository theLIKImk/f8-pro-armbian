"""Compare the original isolated AIQ with an opt-in RT-thread fallback."""
import argparse,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--v32',action='store_true');args=parser.parse_args()
base=(P/'tools/test-f8-camera-c4-back-aiq.sh').read_text()
base=base.replace('back-aiq-trial.log','back-aiq-sched-trial.log').replace('back-aiq02-640x480.nv12','back-aiq04-640x480.nv12')
anchor="root=Path('/opt/f8-pro-camera/aiq-v6-c4');folder=Path('/run/f8-camera-c4')\n"
install='''import hashlib
shim=Path('/opt/f8-pro-camera/aiq-v6-c4/lib/libf8-aiq-sched.so');assert not shim.exists()
data=Path('/home/f8test/.cache/f8-camera-aiq-c4-stage/libf8-aiq-sched.so').read_bytes()
assert hashlib.sha256(data).hexdigest()=='e59464efd82de9ec8f097ceeafc8419434f92be2342d6ed9d44ccead4f8beac5'
shim.write_bytes(data);shim.chmod(0o644)
trial_env={**os.environ,'LD_PRELOAD':str(shim),'F8_AIQ_NORMAL_SCHED_FALLBACK':'1'}
'''
assert base.count(anchor)==1;base=base.replace(anchor,anchor+install)
base=base.replace("stderr=subprocess.STDOUT,start_new_session=True)","stderr=subprocess.STDOUT,start_new_session=True,env=trial_env)")
suffix='v32-sched' if args.v32 else 'sched'
if args.v32:
    base=base.replace('assert not shim.exists()','assert shim.exists()')
    base=base.replace('shim.write_bytes(data);shim.chmod(0o644)','assert shim.read_bytes()==data')
    base=base.replace("lib=C.CDLL('/opt/f8-pro-camera/aiq-v6-c4/lib/librkaiq.so')","lib=C.CDLL('/opt/f8-pro-camera/aiq-v32-c4/lib/librkaiq.so')")
    base=base.replace('back-aiq-sched-trial.log','back-aiq-v32-sched-trial.log').replace('back-aiq04-640x480.nv12','back-aiq05-640x480.nv12')
runner=P/f'local/hardware/camera-c4-back-aiq-{suffix}-runner.sh';assert not runner.exists();runner.write_text(base)
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=90)
assert r.returncode==0,r.stderr
(P/f'local/hardware/camera-c4-back-aiq-{suffix}-test01.json').write_text(r.stdout)
print(f'Saved camera-c4-back-aiq-{suffix}-test01.json')
