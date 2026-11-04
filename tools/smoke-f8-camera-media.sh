#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess,time
from pathlib import Path
assert os.getuid()==1601
runtime=Path('/run/user/1601');sockets=[p.name for p in runtime.glob('wayland-*') if p.is_socket()];assert sockets
folder=Path.home()/'.cache/f8-camera-media-test02';assert not folder.exists();folder.mkdir()
env={**os.environ,'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus','WAYLAND_DISPLAY':sockets[0],'QT_QPA_PLATFORM':'wayland'}
out={}
p=subprocess.run(['/usr/local/bin/f8-camera-preview','--autostart','--quit-after','5','--media-test-dir',str(folder)],capture_output=True,text=True,env=env,timeout=35)
out['app']={'exit':p.returncode,'stdout':p.stdout[-1000:],'stderr':p.stderr[-3500:]}
out['status']=json.loads((runtime/'f8-camera-preview-status.json').read_text())
out['files']=[{'name':p.name,'bytes':p.stat().st_size} for p in folder.iterdir()]
videos=list(folder.glob('*.avi'))
if videos:
 p=subprocess.run(['timeout','-s','INT','-k','2','12','gst-launch-1.0','-v','filesrc','location='+str(videos[0]),'!','avidemux','!','jpegdec','!','identity','silent=false','!','fakesink','sync=false'],capture_output=True,text=True,timeout=17)
 out['decode']={'exit':p.returncode,'identity_chain_count':p.stdout.count('chain   '),'stdout_tail':p.stdout[-1800:],'stderr':p.stderr[-1800:]}
out['leftover']=subprocess.run(['pgrep','-af','aiq-backend|v4l2-ctl|gst-launch'],capture_output=True,text=True).stdout
print(json.dumps(out,indent=2))
PY
