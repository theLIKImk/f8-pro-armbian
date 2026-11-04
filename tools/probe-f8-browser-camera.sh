#!/bin/sh
set -eu
python3 -I - <<'PY'
import http.server,json,os,signal,subprocess,tempfile,threading,time
from pathlib import Path
assert os.getuid()==1601
folder=Path(tempfile.mkdtemp(prefix='f8-browser-camera-03-',dir='/tmp'));result={};done=threading.Event()
page='''<!doctype html><meta charset="utf-8"><video id="v" autoplay muted playsinline></video><pre id="out"></pre><script>
const r={secure:isSecureContext,stage:'start',frames:0};let sent=false;
function report(){document.querySelector('#out').textContent=JSON.stringify(r);if(!sent){sent=true;fetch('/result',{method:'POST',body:JSON.stringify(r)});}}
setTimeout(()=>{r.timeout=true;report()},18000);
(async()=>{try{
 r.stage='permission';let s=await navigator.mediaDevices.getUserMedia({video:true,audio:false});s.getTracks().forEach(t=>t.stop());
 r.stage='enumeration';const d=await navigator.mediaDevices.enumerateDevices();r.cameras=d.filter(x=>x.kind==='videoinput').map(x=>x.label);
 const camera=d.find(x=>x.kind==='videoinput'&&x.label.includes('F8 Camera Relay'));if(!camera)throw Error('Relay camera not found');
 r.stage='capture';s=await navigator.mediaDevices.getUserMedia({video:{deviceId:{exact:camera.deviceId},width:{ideal:640},height:{ideal:480},frameRate:{ideal:14}},audio:true});
 const t=s.getVideoTracks()[0],settings=t.getSettings();r.settings={width:settings.width,height:settings.height,frameRate:settings.frameRate};const v=document.querySelector('#v');v.srcObject=s;await v.play();r.stage='frames';
 let recording=false;
 function frame(now,metadata){r.frames++;r.mediaTime=metadata.mediaTime;if(r.frames===30&&!recording){recording=true;r.stage='recording';const chunks=[];const recorder=new MediaRecorder(s);recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};recorder.onstop=()=>{const blob=new Blob(chunks,{type:recorder.mimeType});r.recording={bytes:blob.size,mime:recorder.mimeType,audioTracks:s.getAudioTracks().length,chunks:chunks.length};r.stage='complete';s.getTracks().forEach(t=>t.stop());report()};recorder.onerror=e=>{r.error={name:e.error.name,message:e.error.message};report()};recorder.start(500);setTimeout(()=>recorder.stop(),3000)}if(!sent)v.requestVideoFrameCallback(frame)}v.requestVideoFrameCallback(frame);
}catch(e){r.error={name:e.name,message:e.message};report()}})();</script>'''.encode()
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(page)));self.end_headers();self.wfile.write(page)
 def do_POST(self):
  try:result.update(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
  finally:self.send_response(204);self.end_headers();done.set()
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
state=Path('/run/user/1601/f8-camera-preview-status.json');before=json.loads(state.read_text())
env={**os.environ,'XDG_RUNTIME_DIR':'/run/user/1601','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus','LD_PRELOAD':'/usr/local/lib/f8-pro/libf8-camera-relay-view.so'}
args=['chromium','--headless=new','--no-first-run','--no-default-browser-check','--disable-background-networking','--use-fake-ui-for-media-stream','--enable-logging=stderr','--vmodule=*video_capture*=2','--user-data-dir='+str(folder/'profile'),'http://127.0.0.1:'+str(server.server_address[1])+'/']
log=folder/'browser.log'
with log.open('w') as output:
 browser=subprocess.Popen(args,env=env,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
 try:done.wait(24)
 finally:
  if browser.poll() is None:
   os.killpg(browser.pid,signal.SIGTERM)
   try:browser.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(browser.pid,signal.SIGKILL);browser.wait()
server.shutdown();server.server_close()
print(json.dumps({'scope':'Fresh profile, loopback test page, genuine camera frames, default browser sandbox. Media permission auto-grant only for isolated probe; no fake camera.','folder':str(folder),'result':result,'before':{'frames':before.get('frames'),'capture_pid':before.get('capture_pid')},'after':json.loads(state.read_text()),'browser_log_tail':log.read_text(errors='replace')[-16000:]},indent=2))
PY
