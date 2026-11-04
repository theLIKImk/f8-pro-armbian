#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess
from pathlib import Path
assert os.getuid()==1601
runtime=Path('/run/user/1601');sockets=[p.name for p in runtime.glob('wayland-*') if p.is_socket()];assert sockets
env={**os.environ,'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus','WAYLAND_DISPLAY':sockets[0],'QT_QPA_PLATFORM':'wayland'}
out={}
for camera,seconds in [('front',10),('back',5)]:
 busy=subprocess.run(['fuser','/dev/video22','/dev/video31'],capture_output=True,text=True);assert not busy.stdout.strip()
 folder=Path.home()/('.cache/f8-'+camera+'-media-test03');assert not folder.exists();folder.mkdir()
 p=subprocess.run(['/usr/local/bin/f8-camera-preview','--camera',camera,'--autostart','--quit-after',str(seconds),'--media-test-dir',str(folder),'--snapshot',str(folder/'window.png')],capture_output=True,text=True,env=env,timeout=30)
 result={'app_exit':p.returncode,'stderr':p.stderr[-2500:],'status':json.loads((runtime/'f8-camera-preview-status.json').read_text()),'files':[{'name':p.name,'bytes':p.stat().st_size} for p in folder.iterdir()]}
 videos=list(folder.glob('*.avi'))
 if videos:
  p=subprocess.run(['timeout','-s','INT','-k','2','12','gst-launch-1.0','-v','filesrc','location='+str(videos[0]),'!','avidemux','!','jpegdec','!','identity','silent=false','!','fakesink','sync=false'],capture_output=True,text=True,timeout=17)
  result['decode']={'exit':p.returncode,'frames':p.stdout.count('chain   '),'eos':'Got EOS' in p.stdout,'stderr':p.stderr[-1200:]}
 out[camera]=result
out['leftover']=subprocess.run(['pgrep','-af','aiq-backend|v4l2-ctl|gst-launch'],capture_output=True,text=True).stdout
print(json.dumps(out,indent=2))
PY
