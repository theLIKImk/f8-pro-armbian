"""One bounded, non-grabbing touchscreen capture, explicitly started by test UI."""
import fcntl,json,os,select,stat,struct,time
from pathlib import Path

W=Path('/var/lib/f8-pro/touch-diagnostic/r2')
W.mkdir(parents=True,exist_ok=True);W.chmod(0o700)
flag=Path('/run/f8-touch-diagnostic/start')
event=next(p for p in Path('/sys/class/input').glob('event*') if (p/'device/name').read_text().strip()=='f8-gsl-shuping')
fd=os.open('/dev/input/'+event.name,os.O_RDONLY|os.O_NONBLOCK|os.O_CLOEXEC)
# Only change this reader's timestamp clock; never grab or alter device events.
fcntl.ioctl(fd,0x400445a0,struct.pack('i',1))
fmt=struct.Struct('llHHi');assert fmt.size==24
slots={};slot=0;pending=b'';frames=0;drops=0;presses=0;releases=0;peak=0
def snap():
 global slot
 a=bytearray(24);fcntl.ioctl(fd,(2<<30)|(24<<16)|(69<<8)|(0x40+0x2f),a,True)
 slot,minimum,maximum,*_=struct.unpack('6i',a)
 values={}
 for code in [0x39,0x35,0x36]:
  a=bytearray(struct.pack('i',code)+b'\0'*(4*(maximum+1)))
  fcntl.ioctl(fd,(2<<30)|(len(a)<<16)|(69<<8)|0x0a,a,True)
  values[code]=struct.unpack_from(str(maximum+1)+'i',a,4)
 for i,ident in enumerate(values[0x39]):
  if ident>=0:slots[i]={'id':ident,'x':values[0x35][i],'y':values[0x36][i]}
snap()
summary={'device':event.name,'non_grabbing':True,'keyboard_accessed':False,'complete':False,'phase':'waiting_for_user_button'}
def save():
 p=W/'summary.json';p.write_text(json.dumps(summary,indent=2)+'\n');p.chmod(0o600)
save()
trace=(W/'frames.jsonl').open('w',buffering=1);os.chmod(W/'frames.jsonl',0o600)
start=None;deadline=time.monotonic()+300;last_save=0;changes=[]
try:
 while time.monotonic()<deadline:
  if start is None:
   assert stat.S_ISREG(flag.lstat().st_mode) and not flag.is_symlink()
   value=flag.read_text().strip()
   if value!='0':
    start=float(value);assert abs(time.monotonic()-start)<10
    deadline=start+65;summary.update(phase='capturing',start_monotonic=start)
    trace.write(json.dumps({'kind':'start','t':start,'slots':slots})+'\n');save()
  ready,_,_=select.select([fd],[],[],.05)
  if ready:
   pending+=os.read(fd,fmt.size*256)
   while len(pending)>=fmt.size:
    sec,usec,kind,code,value=fmt.unpack_from(pending);pending=pending[fmt.size:]
    t=sec+usec/1e6
    if kind==3:
     if code==0x2f:slot=value
     elif code==0x39:
      if value<0:
       old=slots.pop(slot,None)
       if start is not None:releases+=1;changes.append({'action':'up','slot':slot,'old':old})
      else:
       old=slots.get(slot,{}).get('id');slots.setdefault(slot,{})['id']=value
       if start is not None:presses+=1;changes.append({'action':'down','slot':slot,'id':value,'previous_id':old})
     elif code in [0x35,0x36]:slots.setdefault(slot,{})['x' if code==0x35 else 'y']=value
    elif kind==0 and code==3:
     if start is not None:drops+=1;trace.write(json.dumps({'kind':'dropped','t':t})+'\n')
     slots.clear();snap()
    elif kind==0 and code==0:
     if start is not None:
      points=[dict(slot=n,**v) for n,v in sorted(slots.items()) if 'id' in v]
      frames+=1;peak=max(peak,len(points))
      trace.write(json.dumps({'kind':'frame','t':t,'received':time.monotonic(),'points':points,'changes':changes})+'\n')
     changes=[]
  if time.monotonic()-last_save>2:
   summary.update(frames=frames,presses=presses,releases=releases,dropped=drops,peak_contacts=peak);save();last_save=time.monotonic()
 summary.update(complete=start is not None,phase='finished' if start else 'expired_without_start')
finally:
 os.close(fd);trace.close();summary.update(frames=frames,presses=presses,releases=releases,dropped=drops,peak_contacts=peak,ended_monotonic=time.monotonic());save()
