#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/1601
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus
if systemctl --user is-active --quiet f8-kamoso-review01.service; then
 systemctl --user stop f8-kamoso-review01.service
fi
python3 -I - <<'PY'
import json,os,signal,subprocess,time
from pathlib import Path
log=Path.home()/'.cache/f8-kamoso/stream-probe05.log'
out={}
with log.open('w') as f:
 engine=subprocess.Popen(['/usr/bin/python3','-u','/usr/local/lib/f8-pro/aiq-backend.py'],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'LD_PRELOAD':'/opt/f8-pro-camera/aiq-v6-c4/lib/libf8-aiq-otp.so'})
 try:
  for _ in range(70):
   if 'F8_CAMERA_AIQ_READY ' in log.read_text():break
   assert engine.poll() is None;time.sleep(.1)
  assert 'F8_CAMERA_AIQ_READY /dev/video22' in log.read_text()
  for fmt in []:
   p=subprocess.run(['timeout','-s','INT','-k','2','8','v4l2-ctl','-d','/dev/video22','--set-fmt-video=width=640,height=480,pixelformat='+fmt,'--stream-mmap=4','--stream-poll','--stream-count=28','--stream-to=/dev/null'],capture_output=True,text=True,timeout=12)
   out['v4l2-'+fmt]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
  for label,fmt in [('nv12','NV12')]:
   if label!='nv12':break
   args=['timeout','-s','INT','-k','2','12','gst-launch-1.0','-v','v4l2src','device=/dev/video22','io-mode=mmap','num-buffers=28','do-timestamp=true','!','video/x-raw,format=NV12,width=640,height=480,framerate=14/1','!','fakesink','sync=false']
   p=subprocess.run(args,capture_output=True,text=True,timeout=17,env={**os.environ,'GST_DEBUG':'v4l2:4,v4l2bufferpool:5','LD_PRELOAD':str(Path.home()/'.cache/f8-kamoso/libgst-buffer-trial.so')});out[label]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr[-22000:]}
  p=subprocess.run(['timeout','-s','INT','-k','2','8','v4l2-ctl','-d','/dev/video22','--set-fmt-video=width=640,height=480,pixelformat=NV12','--stream-mmap=4','--stream-poll','--stream-count=28','--stream-to=/dev/null'],capture_output=True,text=True,timeout=12)
  out['v4l2-ctl']={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 finally:
  engine.terminate()
  try:engine.wait(timeout=6)
  except subprocess.TimeoutExpired:engine.kill();engine.wait()
  out['engine_exit']=engine.returncode
out['engine_log']=log.read_text()[-3000:]
print(json.dumps(out,indent=2))
PY
