"""Derived back IQ: change only AE frame-rate policy, preserve factory calibration."""
import argparse,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--v32',action='store_true');args=parser.parse_args()
s=(P/'tools/test-f8-camera-c4-back-aiq.sh').read_text()
s=s.replace('back-aiq-trial.log','back-aiq-fps14.log').replace('back-aiq02-640x480.nv12','back-aiq-fps14-640x480.nv12')
s=s.replace("b'/opt/f8-pro-camera/aiq-v6-c4/iqfiles'","b'/opt/f8-pro-camera/aiq-v6-c4/iqfiles-fps14'")
anchor="root=Path('/opt/f8-pro-camera/aiq-v6-c4');folder=Path('/run/f8-camera-c4')\n"
patch='''derived=root/'iqfiles-fps14';assert not derived.exists();derived.mkdir()
name='ov8858_HS5885-BNSM1018-V01_default.json'
original=json.loads((root/'iqfiles'/name).read_text());changed=json.loads(json.dumps(original))
rate=changed['main_scene'][0]['sub_scene'][0]['scene_isp30']['ae_calib']['CommCtrl']['AecFrameRateMode']
assert rate=={'isFpsFix':0,'FpsValue':0}
rate.update(isFpsFix=1,FpsValue=14)
(derived/name).write_text(json.dumps(changed)+'\\n')
'''
assert s.count(anchor)==1;s=s.replace(anchor,anchor+patch)
suffix='fps14-v32' if args.v32 else 'fps14'
if args.v32:
    s=s.replace("derived=root/'iqfiles-fps14';assert not derived.exists();derived.mkdir()", "derived=root/'iqfiles-fps14';assert derived.is_dir()")
    s=s.replace("(derived/name).write_text(json.dumps(changed)+'\\n')", "assert json.loads((derived/name).read_text())==changed")
    s=s.replace("lib=C.CDLL('/opt/f8-pro-camera/aiq-v6-c4/lib/librkaiq.so')","lib=C.CDLL('/opt/f8-pro-camera/aiq-v32-c4/lib/librkaiq.so')")
    s=s.replace('back-aiq-fps14.log','back-aiq-fps14-v32.log').replace('back-aiq-fps14-640x480.nv12','back-aiq-fps14-v32-640x480.nv12')
    s=s.replace('stderr=subprocess.STDOUT,start_new_session=True)', "stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'LD_PRELOAD':'/opt/f8-pro-camera/aiq-v6-c4/lib/libf8-aiq-sched.so','F8_AIQ_NORMAL_SCHED_FALLBACK':'1'})")
runner=P/f'local/hardware/camera-c4-aiq-{suffix}-runner.sh';assert not runner.exists();runner.write_text(s)
p=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=90)
assert p.returncode==0,p.stderr
(P/f'local/hardware/camera-c4-aiq-{suffix}-test01.json').write_text(p.stdout)
print(f'Saved {suffix} trial')
