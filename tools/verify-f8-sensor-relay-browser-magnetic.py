import subprocess,time,json,os,errno,struct
from pathlib import Path
p=Path('/etc/udev/rules.d/72-f8-sensor-relay.rules');p.write_text(p.read_text().replace('MODE="0600"','MODE="0660"'))
subprocess.run(['udevadm','control','--reload-rules'],check=True)
subprocess.run(['udevadm','trigger','--action=add','--subsystem-match=misc','--sysname-match=f8-sensor-feed'],check=True)
subprocess.run(['udevadm','settle'],check=True)
time.sleep(2)
s=json.loads(Path('/run/user/1602/f8-sensor-relay.json').read_text());assert s['online'] and s['iio_feed_connected'],s
p=next(p for p in Path('/sys/bus/iio/devices').glob('iio:device*') if (p/'name').read_text().strip()=='f8-sensor-relay')
out={'snapshot':{k:s.get(k) for k in ['online','valid','absolute_valid','iio_feed_connected','acceleration_m_s2','angular_velocity_rad_s','brightness']},'relay':str(p),'raw':{x.name:x.read_text().strip() for x in p.glob('*_raw')},'udev':subprocess.check_output(['udevadm','info','--query=property','--path='+str(p)],text=True),'feed_acl':subprocess.check_output(['getfacl','-p','/dev/f8-sensor-feed'],text=True)}
# Verify actual measured buffered transport, then restore all scan controls.
saved={x:x.read_text().strip() for x in (p/'scan_elements').glob('*_en')};saved_enable=(p/'buffer/enable').read_text().strip()
try:
 (p/'buffer/enable').write_text('0')
 for x in saved:x.write_text('1')
 (p/'buffer/enable').write_text('1')
 fd=os.open('/dev/'+p.name,os.O_RDONLY|os.O_NONBLOCK)
 try:
  time.sleep(.2);b=os.read(fd,320);out['buffer']={'bytes':len(b),'first_frame':struct.unpack('=9i4xq',b[:48])}
 finally:os.close(fd)
finally:
 (p/'buffer/enable').write_text('0')
 for x,v in saved.items():x.write_text(v)
 (p/'buffer/enable').write_text(saved_enable)
print(json.dumps({'native':out}))

import http.server,json,os,pwd,subprocess,tempfile,threading,time
from pathlib import Path
account=pwd.getpwnam('likimk')
folder=Path(tempfile.mkdtemp(prefix='f8-browser-sensor-probe-',dir='/tmp'));os.chown(folder,account.pw_uid,account.pw_gid)
page=folder/'probe.html'
page.write_text('''<!doctype html><meta charset="utf-8"><pre id="out"></pre><script>
const r={secure:window.isSecureContext,visibility:document.visibilityState,apis:{},permissions:{}};
function show(){document.getElementById('out').textContent=JSON.stringify(r);}
for(const name of ['Accelerometer','Gyroscope','Magnetometer','RelativeOrientationSensor','AbsoluteOrientationSensor','DeviceMotionEvent','DeviceOrientationEvent']){
 r.apis[name]={exposed:typeof window[name]!=='undefined'};
 if(!r.apis[name].exposed || name.endsWith('Event'))continue;
 try{const s=new window[name]({frequency:5});s.addEventListener('error',e=>{r.apis[name].error={name:e.error.name,message:e.error.message};show()});s.addEventListener('reading',()=>{r.apis[name].reading=true;r.apis[name].count=(r.apis[name].count||0)+1;r.apis[name].values=s.quaternion?Array.from(s.quaternion):[s.x,s.y,s.z];show()});s.start();}
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
args=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus',
 'chromium','--enable-blink-features=SensorExtraClasses','--headless','--no-first-run','--no-default-browser-check','--disable-background-networking',
 '--user-data-dir='+str(folder/'profile'),'--dump-dom','http://127.0.0.1:'+str(server.server_address[1])+'/']
try:
 p=subprocess.run(args,capture_output=True,text=True,timeout=30)
 print(json.dumps({'exit':p.returncode,'html':p.stdout,'stderr':p.stderr[-7000:],
  'scope':'Fresh temporary profile, secure loopback page, default sandbox, six real seconds for discovery; no existing profile or remote pages opened.'},indent=2))
except subprocess.TimeoutExpired:
 print(json.dumps({'error':'isolated headless probe timed out','scope':'existing browser left untouched'}))
finally:
 server.shutdown();server.server_close()