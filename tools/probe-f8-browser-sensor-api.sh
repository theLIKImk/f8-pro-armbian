#!/bin/sh
set -eu
python3 -I - <<'PY'
import http.server,json,os,pwd,subprocess,tempfile,threading,time
from pathlib import Path
account=pwd.getpwnam('f8test')
folder=Path(tempfile.mkdtemp(prefix='f8-browser-sensor-probe-',dir='/tmp'));os.chown(folder,account.pw_uid,account.pw_gid)
page=folder/'probe.html'
page.write_text('''<!doctype html><meta charset="utf-8"><pre id="out"></pre><script>
const r={secure:window.isSecureContext,visibility:document.visibilityState,apis:{},permissions:{}};
function show(){document.getElementById('out').textContent=JSON.stringify(r);}
for(const name of ['Accelerometer','Gyroscope','Magnetometer','RelativeOrientationSensor','AbsoluteOrientationSensor','DeviceMotionEvent','DeviceOrientationEvent']){
 r.apis[name]={exposed:typeof window[name]!=='undefined'};
 if(!r.apis[name].exposed || name.endsWith('Event'))continue;
 try{const s=new window[name]({frequency:5});s.addEventListener('error',e=>{r.apis[name].error={name:e.error.name,message:e.error.message};show()});s.addEventListener('reading',()=>{r.apis[name].reading=true;show()});s.start();}
 catch(e){r.apis[name].exception={name:e.name,message:e.message};}
}
for(const n of ['accelerometer','gyroscope','magnetometer'])navigator.permissions.query({name:n}).then(p=>{r.permissions[n]=p.state;show()}).catch(e=>{r.permissions[n]=e.name;show()});
show();setTimeout(show,2500);
</script><script src="/wait.js"></script>''')
page.chmod(0o644)
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path=='/wait.js':time.sleep(6);data=b'// Allow native sensor discovery six seconds of real time.';kind='application/javascript'
  else:data=page.read_bytes();kind='text/html; charset=utf-8'
  self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
args=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus',
 'chromium','--headless','--no-first-run','--no-default-browser-check','--disable-background-networking',
 '--user-data-dir='+str(folder/'profile'),'--dump-dom','http://127.0.0.1:'+str(server.server_address[1])+'/']
try:
 p=subprocess.run(args,capture_output=True,text=True,timeout=30)
 print(json.dumps({'exit':p.returncode,'html':p.stdout,'stderr':p.stderr[-7000:],
  'scope':'Fresh temporary profile, secure loopback page, default sandbox, six real seconds for discovery; no existing profile or remote pages opened.'},indent=2))
except subprocess.TimeoutExpired:
 print(json.dumps({'error':'isolated headless probe timed out','scope':'existing browser left untouched'}))
finally:
 server.shutdown();server.server_close()
PY
