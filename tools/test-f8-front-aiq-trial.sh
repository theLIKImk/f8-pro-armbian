#!/bin/sh
set -eu
python3 -I - <<'PY'
import ctypes as C,json,os,subprocess,time
from pathlib import Path
assert os.getuid()==1601
stage=Path.home()/'.cache/f8-kamoso';folder=Path.home()/'.cache/f8-front-aiq-trial02';assert not folder.exists();folder.mkdir()
busy=subprocess.run(['fuser','/dev/video22','/dev/video31','/dev/video0'],capture_output=True,text=True);assert not busy.stdout.strip(),busy.stdout
env={**os.environ,'XDG_RUNTIME_DIR':'/run/user/1601','LD_PRELOAD':'/opt/f8-pro-camera/aiq-v6-c4/lib/libf8-aiq-otp.so'}
out={};log=folder/'engine.log'
with log.open('w') as f:
 engine=subprocess.Popen(['/usr/bin/python3','-u',str(stage/'aiq-backend.py'),'--camera','front'],env=env,stdout=f,stderr=subprocess.STDOUT)
 try:
  for _ in range(100):
   if 'F8_CAMERA_AIQ_READY ' in log.read_text():break
   if engine.poll() is not None:break
   time.sleep(.1)
  out['ready']='F8_CAMERA_AIQ_READY /dev/video31' in log.read_text()
  if out['ready']:
   file=folder/'front.nv12'
   p=subprocess.run(['timeout','-s','INT','-k','2','13','v4l2-ctl','-d','/dev/video31','--set-fmt-video=width=640,height=480,pixelformat=NV12','--stream-mmap=4','--stream-poll','--stream-count=112','--stream-to='+str(file)],capture_output=True,text=True,timeout=17)
   out['capture']={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
   data=file.read_bytes() if file.exists() else b'';size=460800;out['frames']=len(data)//size;out['bytes']=len(data)
   if len(data)>=size:
    frame=data[-size:];out['last_yuv']={n:{'mean':sum(v)/len(v),'min':min(v),'max':max(v)} for n,v in [('Y',frame[:307200]),('U',frame[307200::2]),('V',frame[307201::2])]}
    lib=C.CDLL('/usr/local/lib/f8-pro/libf8-camera-pixels.so');fn=lib.f8_nv12_rgb;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_uint,C.c_uint];fn.restype=C.c_int
    src=C.create_string_buffer(frame);rgb=C.create_string_buffer(640*480*3);assert fn(src,size,rgb,len(rgb),640,480)==0
    from PyQt6.QtGui import QImage
    image=QImage(rgb.raw,640,480,640*3,QImage.Format.Format_RGB888).copy();assert image.save(str(folder/'front.png'))
   p=subprocess.run(['v4l2-ctl','-d','/dev/v4l-subdev2','--list-ctrls'],capture_output=True,text=True);out['controls_after']=p.stdout
 finally:
  if engine.poll() is None:engine.terminate()
  try:engine.wait(timeout=6)
  except subprocess.TimeoutExpired:engine.kill();engine.wait()
  out['engine_exit']=engine.returncode
out['engine_log']=log.read_text()[-16000:];out['folder']=str(folder)
print(json.dumps(out,indent=2))
PY
