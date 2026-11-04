#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess,time
from pathlib import Path
assert os.getuid()==1601
assert "parser.add_argument('--relay'" in Path('/usr/local/lib/f8-pro/camera-preview.py').read_text(),'Install relay frontend first'
runtime=Path('/run/user/1601');sockets=[p.name for p in runtime.glob('wayland-*') if p.is_socket()];assert sockets
env={**os.environ,'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus','WAYLAND_DISPLAY':sockets[0],'QT_QPA_PLATFORM':'wayland'}
folder=Path.home()/'.cache/f8-relay-test05';assert not folder.exists();folder.mkdir();out={}
for camera in ['front','back']:
 result={};log=folder/(camera+'.log')
 with log.open('w') as f:
  app=subprocess.Popen(['/usr/local/bin/f8-camera-preview','--camera',camera,'--autostart','--relay','--quit-after','11'],stdout=f,stderr=subprocess.STDOUT,env=env)
  try:
   for _ in range(80):
    try:state=json.loads((runtime/'f8-camera-preview-status.json').read_text())
    except (FileNotFoundError,json.JSONDecodeError):state={}
    if state.get('camera')==camera and state.get('relay_running') and state.get('relay_frames',0)>=5:break
    if app.poll() is not None:break
    time.sleep(.1)
   result['ready_state']=state
   p=subprocess.run(['timeout','-s','INT','-k','2','7','gst-launch-1.0','-v','v4l2src','device=/dev/video42','io-mode=mmap','num-buffers=28','!','video/x-raw,format=YUY2,width=640,height=480,framerate=14/1','!','identity','silent=false','!','fakesink','sync=false'],capture_output=True,text=True,timeout=11,env={**env,'LD_PRELOAD':'/usr/local/lib/f8-pro/libf8-camera-relay-view.so'})
   result['consumer']={'exit':p.returncode,'frames':p.stdout.count('chain   '),'eos':'Got EOS' in p.stdout,'stdout_tail':p.stdout[-1200:],'stderr':p.stderr[-2000:]}
   app.wait(timeout=16)
  finally:
   if app.poll() is None:
    app.terminate()
    try:app.wait(timeout=8)
    except subprocess.TimeoutExpired:app.kill();app.wait()
  result['app_exit']=app.returncode
 result['app_log']=log.read_text()[-2000:];result['final_state']=json.loads((runtime/'f8-camera-preview-status.json').read_text());out[camera]=result
out['leftover']=subprocess.run(['pgrep','-af','aiq-backend|v4l2-ctl|gst-launch'],capture_output=True,text=True).stdout
print(json.dumps(out,indent=2))
PY
