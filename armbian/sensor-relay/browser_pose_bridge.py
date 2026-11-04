#!/usr/bin/python3
"""Feed only live F8 fused poses to a child Chromium through a private CDP pipe.
No listening debug port, JS injection, grants or browser sandbox changes.
"""
import json,os,sys,subprocess,selectors,time,signal,math,collections
from pathlib import Path
from browser_pose_math import quaternion_xyzw,device_euler

class PoseBrowser:
 def __init__(self,args,env,log):
  cr,cw=os.pipe();rr,rw=os.pipe()
  def child_fds():os.dup2(cr,3);os.dup2(rw,4)
  self.child=subprocess.Popen(args+['--remote-debugging-pipe'],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,pass_fds=tuple(set((3,4,cr,rw))),preexec_fn=child_fds)
  os.close(cr);os.close(rw);self.write=cw;self.read=rr;os.set_blocking(rr,False);self.selector=selectors.DefaultSelector();self.selector.register(rr,selectors.EVENT_READ)
  self.buffer=b'';self.ident=0;self.sessions={};self.pending={};self.last_state=None;self.last_poll=0;self.status_at=0;self.errors={};self.rpc=None;self.alive=True;self.log=log;self.last_good=None;self.transitions=collections.deque(maxlen=64);self.site_fix=Path(__file__).with_name('codertools-motion-fix.js').read_text(encoding='utf-8-sig')
  self.runtime=Path(os.environ.get('XDG_RUNTIME_DIR','/tmp'))/'f8-browser-pose.json'
  self.send('Target.setAutoAttach',{'autoAttach':True,'waitForDebuggerOnStart':True,'flatten':True})
 def send(self,method,params=None,session=None):
  self.ident+=1;d={'id':self.ident,'method':method,'params':params or {}}
  if session:d['sessionId']=session
  self.pending[self.ident]=(method,session)
  b=json.dumps(d,separators=(',',':')).encode()+b'\0'
  while b:b=b[os.write(self.write,b):]
 def poll_state(self,now):
  self.last_poll=now
  # Read the daemon's atomic, user-private snapshot. Its timestamp is the physical IMU timestamp.
  try:
   if self.rpc is None:
    import dbus
    self.bus=dbus.SessionBus();self.rpc=dbus.Interface(self.bus.get_object('net.f8.Sensors','/net/f8/Sensors'),'net.f8.Sensors1')
   try:s=json.loads(str(self.rpc.GetSnapshot(timeout=.25)))
   except Exception:
    self.rpc=None;s=json.loads((Path(os.environ['XDG_RUNTIME_DIR'])/'f8-sensor-relay.json').read_text())
   fresh=0<=time.monotonic()-s.get('monotonic',0)<.65 and s.get('online') and s.get('relay_enabled') and s.get('valid')
  except Exception:self.rpc=None;s={};fresh=False
  held=False
  if fresh:self.last_good=dict(s)
  elif s.get('relay_enabled') and self.last_good and time.monotonic()-self.last_good.get('monotonic',0)<1.2:
   s=dict(self.last_good);fresh=True;held=True
  q=quaternion_xyzw(s.get('game_rotation_vector_wxyz')) if fresh else None
  qa=quaternion_xyzw(s.get('rotation_vector_wxyz')) if fresh and s.get('absolute_valid') else None
  self.last_state={'available':bool(q),'absolute_available':bool(qa),'relative':q,'absolute':qa,'euler':device_euler(s.get('game_rotation_vector_wxyz')) if q else None,'source_monotonic':s.get('monotonic'),'gyro_stationary':s.get('gyro_stationary'),'held_while_source_recovers':held}
  for session in list(self.sessions):self.publish(session,self.last_state)
 def publish(self,session,state):
  target=self.sessions.get(session)
  if target is None:return
  for name,key,avail_key in [('relative-orientation','relative','available'),('absolute-orientation','absolute','absolute_available')]:
   available=state[avail_key]
   if target.get(name) is not available:
    if name=='relative-orientation':self.transitions.append({'monotonic':time.monotonic(),'available':available,'source_age':time.monotonic()-(state.get('source_monotonic') or 0)})
    if name in target:self.send('Emulation.setSensorOverrideEnabled',{'type':name,'enabled':False},session)
    self.send('Emulation.setSensorOverrideEnabled',{'type':name,'enabled':True,'metadata':{'available':available,'minimumFrequency':1,'maximumFrequency':20}},session);target[name]=available
   if available:
    x,y,z,w=state[key];self.send('Emulation.setSensorOverrideReadings',{'type':name,'reading':{'quaternion':{'x':x,'y':y,'z':z,'w':w}}},session)
 def message(self,m):
  if 'id' in m:
   method,session=self.pending.pop(m['id'],('unknown',None))
   if 'error' in m:self.errors[method]=m['error']
   else:
    self.errors.pop(method,None)
   return
  if m.get('method')=='Target.attachedToTarget':
   p=m['params'];sid=p['sessionId'];kind=p.get('targetInfo',{}).get('type')
   if kind in ['page','iframe']:
    self.sessions[sid]={}
    self.send('Page.addScriptToEvaluateOnNewDocument',{'source':self.site_fix,'runImmediately':True},sid)
    if self.last_state:self.publish(sid,self.last_state)
    self.send('Target.setAutoAttach',{'autoAttach':True,'waitForDebuggerOnStart':True,'flatten':True},sid)
   self.send('Runtime.runIfWaitingForDebugger',{},sid)
  elif m.get('method')=='Target.detachedFromTarget':self.sessions.pop(m['params']['sessionId'],None)
 def status(self,now,online=True):
  try:
   data={'version':1,'online':online,'browser_pid':self.child.pid,'monotonic':now,'page_targets':len(self.sessions),'source':self.last_state,'protocol_errors':self.errors,'transport':'private child pipe; no TCP port','permission_grants_changed':False,'availability_transitions':list(self.transitions)[-20:]}
   p=self.runtime.with_suffix('.tmp');fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
   with os.fdopen(fd,'w') as f:json.dump(data,f)
   os.replace(p,self.runtime)
  except OSError:pass
 def run(self):
  try:
   while self.alive and self.child.poll() is None:
    now=time.monotonic()
    if now-self.last_poll>=.05:self.poll_state(now)
    if now-self.status_at>=.5:self.status_at=now;self.status(now)
    for _,_ in self.selector.select(.03):
     b=os.read(self.read,262144)
     if not b:self.alive=False;break
     self.buffer+=b
     while b'\0' in self.buffer:
      part,self.buffer=self.buffer.split(b'\0',1)
      if part:
       try:self.message(json.loads(part))
       except (ValueError,KeyError) as e:self.errors['decode']=str(e)
   if self.child.poll() is None:self.child.terminate()
   return self.child.wait(timeout=10)
  finally:
   self.status(time.monotonic(),False);self.selector.close();os.close(self.read);os.close(self.write)
   if self.child.poll() is None:self.child.terminate();self.child.wait(timeout=10)

def launch(args,env,log):
 p=PoseBrowser(args,env,log)
 def stop(*_):p.alive=False
 for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,stop)
 return p.run()
