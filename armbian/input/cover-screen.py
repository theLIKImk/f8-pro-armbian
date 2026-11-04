#!/usr/bin/python3
"""Normal-user machine-cover observer; optional screen DPMS, never suspend/unlock."""
import fcntl,json,os,select,signal,struct,subprocess,time
from pathlib import Path
runtime=Path(os.environ['XDG_RUNTIME_DIR']);folder=Path.home()/'.cache/f8-cover';folder.mkdir(parents=True,exist_ok=True)
config=Path.home()/'.config/f8-cover.json';status=folder/'status.json';events=[];count=0;error='';action=None;enabled=False;last=None
fd=os.open('/dev/input/f8-cover',os.O_RDONLY|os.O_NONBLOCK)
def current():
 data=bytearray(4);fcntl.ioctl(fd,0x8004451b,data,True);return bool(int.from_bytes(data,'little')&(1<<16))
def mode():
 try:c=json.loads(config.read_text());return c.get('validated',False) and c.get('screen_enabled',False)
 except (OSError,ValueError):return False
def display(closed):
 global action,error
 env={**os.environ,'QT_QPA_PLATFORM':'wayland','DBUS_SESSION_BUS_ADDRESS':'unix:path='+str(runtime/'bus')}
 sockets=[p.name for p in runtime.glob('wayland-*') if p.is_socket()]
 if not sockets:action=None;error='Wayland尚未就绪';return
 env['WAYLAND_DISPLAY']=sockets[0]
 try:
  p=subprocess.run(['kscreen-doctor','--dpms','off' if closed else 'on'],env=env,capture_output=True,text=True,timeout=5)
  action=('off' if closed else 'on') if p.returncode==0 else None;error='' if p.returncode==0 else p.stderr[-800:]
 except (OSError,subprocess.TimeoutExpired) as e:action=None;error=str(e)
def write(closed):
 data={'closed':closed,'screen_enabled':enabled,'events_count':count,'recent_events':events[-20:],'last_action':action,'error':error,'heartbeat':time.time()}
 temp=status.with_suffix('.new');temp.write_text(json.dumps(data,ensure_ascii=False));temp.replace(status)
def stop(*_):raise SystemExit(0)
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
closed=current();event=struct.Struct('llHHi');assert event.size==24
try:
 while True:
  updated=mode()
  if updated!=enabled:
   previous=enabled;enabled=updated
   if previous and not enabled:display(False)
   last=None
  if enabled and (last!=closed or action is None):display(closed);last=closed
  write(closed)
  ready,_,_=select.select([fd],[],[],1)
  if ready:
   raw=os.read(fd,event.size*64)
   for pos in range(0,len(raw),event.size):
    sec,usec,kind,code,value=event.unpack_from(raw,pos)
    if kind==5 and code==16:
     closed=bool(value);count+=1;events.append({'closed':closed,'timestamp':sec+usec/1e6})
    elif kind==0 and code==3:closed=current()
finally:
 os.close(fd)
 if enabled:display(False)
