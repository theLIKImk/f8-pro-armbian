#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,signal,subprocess,time
from pathlib import Path
assert os.getuid()==1601
folder=Path('/home/f8test/.cache/f8-camera-aiq-c4-stage')
log=folder/'gst-worker01.log';assert not log.exists()
out={};target=folder/'gst-rgb01.raw';assert not target.exists()
env={**os.environ,'XDG_RUNTIME_DIR':'/run/user/1601','LD_PRELOAD':'/opt/f8-pro-camera/aiq-v6-c4/lib/libf8-aiq-otp.so'}
with log.open('w') as output:
 engine=subprocess.Popen(['python3','-u','/usr/local/lib/f8-pro/aiq-backend.py'],env=env,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
 try:
  for _ in range(50):
   if engine.poll() is not None or 'F8_CAMERA_AIQ_READY ' in log.read_text(errors='replace'):break
   time.sleep(.1)
  out['engine_before_capture']=engine.poll()
  if engine.poll() is None:
   with target.open('wb') as frames:
    cmd=['gst-launch-1.0','-q','v4l2src','device=/dev/video22','io-mode=mmap','num-buffers=45','!',
       'video/x-raw,format=NV12,width=640,height=480','!','videoconvert','!',
       'video/x-raw,format=RGB','!','fdsink','fd=1','sync=false']
    try:
     p=subprocess.run(cmd,stdout=frames,stderr=subprocess.PIPE,timeout=9)
     out['gst']={'exit':p.returncode,'stderr':p.stderr.decode(errors='replace')}
    except subprocess.TimeoutExpired as e:out['gst']={'timeout':True,'stderr':(e.stderr or b'').decode(errors='replace')}
   out['bytes']=target.stat().st_size;out['frames_rgb']=target.stat().st_size/921600
   if target.stat().st_size>=921600:
    with target.open('rb') as f:f.seek(-921600,2);last=f.read()
    target.write_bytes(last);out['retained_bytes']=len(last)
 finally:
  if engine.poll() is None:
   engine.terminate()
   try:engine.wait(timeout=4)
   except subprocess.TimeoutExpired:engine.kill();engine.wait(timeout=2)
out['engine_log']=log.read_text(errors='replace')[-4000:]
print(json.dumps(out,indent=2))
PY
