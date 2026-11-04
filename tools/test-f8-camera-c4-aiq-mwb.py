"""Back-camera diagnostic: factory manual WB gains + fixed14fps, original IQ untouched."""
import subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'local/hardware/camera-c4-aiq-fps14-runner.sh').read_text()
s=s.replace('iqfiles-fps14','iqfiles-fps14-mwb').replace('back-aiq-fps14.log','back-aiq-fps14-mwb.log').replace('back-aiq-fps14-640x480.nv12','back-aiq-fps14-mwb-640x480.nv12')
anchor='rate.update(isFpsFix=1,FpsValue=14)\n'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"changed['main_scene'][0]['sub_scene'][0]['scene_isp30']['wb_v21']['control']['mode']='CALIB_WB_MODE_MANUAL'\n")
r=P/'local/hardware/camera-c4-aiq-mwb-runner.sh';assert not r.exists();r.write_text(s)
p=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(r),'--sudo'],capture_output=True,text=True,timeout=90)
assert p.returncode==0,p.stderr
(P/'local/hardware/camera-c4-aiq-mwb-test01.json').write_text(p.stdout)
print('Saved factory manual-WB comparison')
