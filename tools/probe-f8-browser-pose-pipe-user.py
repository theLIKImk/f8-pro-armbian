"""Isolated live Chromium pipe test, correct pose and permission-policy checks."""
import sys,os,json,threading,http.server,tempfile,time,math
from pathlib import Path
sys.path.insert(0,'/usr/local/lib/f8-pro')
from browser_pose_bridge import PoseBrowser
reports=[]
page='''<!doctype html><meta charset="utf-8"><body><script>
const r={relative:[],absolute:[],legacy:[],errors:[],permission:null};
navigator.permissions.query({name:'accelerometer'}).then(p=>r.permission=p.state);
for (const [key,name] of [['relative','RelativeOrientationSensor'],['absolute','AbsoluteOrientationSensor']]){
 try { const s=new window[name]({frequency:10});s.onreading=()=>{if(s.quaternion)r[key].push(Array.from(s.quaternion));};s.onerror=e=>r.errors.push(e.error.name);s.start(); }catch(e){r.errors.push(e.name);}
}
window.addEventListener('deviceorientation',e=>{r.legacy.push([e.alpha,e.beta,e.gamma]);});
window.addEventListener('message',e=>{if(e.origin===location.origin)r.blocked=e.data;});
setTimeout(()=>fetch('/report',{method:'POST',body:JSON.stringify(r)}),3500);
</script><iframe src="/blocked" allow="accelerometer 'none'; gyroscope 'none'; magnetometer 'none'"></iframe>'''
blocked='''<!doctype html><script>let r={relative:0,legacy:0,errors:[]};try{const s=new RelativeOrientationSensor({frequency:5});s.onreading=()=>r.relative++;s.onerror=e=>r.errors.push(e.error.name);s.start()}catch(e){r.errors.push(e.name)}addEventListener('deviceorientation',()=>r.legacy++);setTimeout(()=>parent.postMessage(r,location.origin),2500)</script>'''
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  b=(blocked if self.path=='/blocked' else page).encode();self.send_response(200);self.send_header('Content-Type','text/html');
  if self.path=='/blocked':self.send_header('Permissions-Policy','accelerometer=(), gyroscope=(), magnetometer=()')
  self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def do_POST(self):
  r=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))));r['native_source']=controller.last_state;reports.append(r);self.send_response(204);self.end_headers()
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);origin='http://127.0.0.1:'+str(server.server_address[1])
class TestBrowser(PoseBrowser):
 def __init__(self,*args):self.start=time.monotonic();self.denied=False;super().__init__(*args)
 def poll_state(self,now):
  super().poll_state(now)
  if len(reports)==1 and not self.denied:
   self.denied=True;self.send('Browser.setPermission',{'permission':{'name':'accelerometer'},'setting':'denied','origin':origin})
   for sid in self.sessions:self.send('Page.reload',{},sid)
  if len(reports)>=2 or now-self.start>22:self.alive=False
with tempfile.TemporaryDirectory(prefix='f8-browser-pose-pipe-') as tmp:
 with open(Path(tmp)/'browser.log','w') as log:
  controller=TestBrowser(['/usr/bin/chromium','--headless','--no-first-run','--no-default-browser-check','--enable-features=GenericSensorExtraClasses','--enable-blink-features=SensorExtraClasses','--user-data-dir='+str(Path(tmp)/'profile'),origin],dict(os.environ),log)
  threading.Thread(target=server.serve_forever,daemon=True).start();exitcode=controller.run()
  log.flush();stderr=(Path(tmp)/'browser.log').read_text()[-3000:]
server.shutdown();server.server_close()
print(json.dumps({'reports':reports,'protocol_errors':controller.errors,'browser_exit':exitcode,'browser_log_tail':stderr}))
