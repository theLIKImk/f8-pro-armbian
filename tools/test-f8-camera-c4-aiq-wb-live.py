"""Apply manual-WB API after frames start, distinguishing prepare-time reset."""
import subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'local/hardware/camera-c4-aiq-wb-api-runner.sh').read_text()
s=s.replace('back-aiq-fps14-apiwb.log','back-aiq-fps14-livewb.log').replace('back-aiq-fps14-apiwb-640x480.nv12','back-aiq-fps14-livewb-640x480.nv12')
anchor='    time.sleep(18)'
patch='''    import threading
    def apply_live_wb():
        value=WB(1.2261,1.0,1.0,2.3158)
        print('LIVE_WB_MODE',lib.rk_aiq_uapi2_setWBMode(ctx,1),flush=True)
        print('LIVE_WB_GAIN',lib.rk_aiq_uapi2_setMWBGain(ctx,C.byref(value)),flush=True)
    timer=threading.Timer(.5,apply_live_wb);timer.start()
    time.sleep(18)'''
assert s.count(anchor)==1;s=s.replace(anchor,patch)
r=P/'local/hardware/camera-c4-aiq-wb-live-runner.sh';assert not r.exists();r.write_text(s)
p=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(r),'--sudo'],capture_output=True,text=True,timeout=90)
assert p.returncode==0,p.stderr
(P/'local/hardware/camera-c4-aiq-wb-live-test01.json').write_text(p.stdout)
print('Saved live-WB API comparison')
