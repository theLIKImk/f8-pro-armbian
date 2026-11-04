"""Bounded IRQ/evdev timing capture, triggered by first contact; no device writes."""
import argparse,fcntl,json,os,pwd,re,select,signal,statistics,struct,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--round',required=True);a=p.parse_args()
assert os.geteuid()==0 and re.fullmatch(r'[a-z0-9-]{1,24}',a.round)
flag=Path('/run/user')/str(pwd.getpwnam('likimk').pw_uid)/('f8-touch-rate-'+a.round+'.start')
assert not flag.exists(),'Preserve earlier start marker'
W=Path('/var/lib/f8-pro/touch-rate')/a.round;assert not W.exists();W.mkdir(parents=True);W.chmod(0o755)
event=next(x for x in Path('/sys/class/input').glob('event*') if (x/'device/name').read_text().strip()=='f8-gsl-shuping')
irq_lines=[l for l in Path('/proc/interrupts').read_text().splitlines() if 'gslx680-shuping' in l]
assert len(irq_lines)==1;irq=int(irq_lines[0].split(':')[0])
T=Path('/sys/kernel/tracing');I=T/'instances'/('f8rate_'+a.round.replace('-','_'));assert not I.exists()
state={'phase':'preparing','round':a.round,'device':event.name,'irq':irq,'non_grabbing':True,'keyboard_accessed':False}
def save():
 q=W/'status.tmp';q.write_text(json.dumps(state,indent=2)+'\n');q.chmod(0o644);q.replace(W/'status.json')
 q=Path('/run')/('f8-touch-rate-'+a.round+'.tmp');assert not q.is_symlink()
 q.write_text(json.dumps(state,indent=2)+'\n');q.chmod(0o644);q.replace(Path('/run')/('f8-touch-rate-'+a.round+'.json'))
def write(path,value):path.write_text(str(value)+'\n')
def interrupted(*_):raise SystemExit('Capture interrupted')
signal.signal(signal.SIGTERM,interrupted)
fd=None;created=False;start=None;frames=[];slots=set();slot=0;drops=0;i2c_enabled=False
try:
 I.mkdir();created=True;write(I/'tracing_on',0);write(I/'trace_clock','mono');write(I/'buffer_size_kb',1024)
 write(I/'events/irq/irq_handler_entry/filter','irq == '+str(irq));write(I/'events/irq/irq_handler_entry/enable',1)
 if (I/'events/i2c/i2c_read/enable').exists():
  write(I/'events/i2c/i2c_read/filter','adapter_nr == 4 && addr == 64 && len == 44')
  write(I/'events/i2c/i2c_result/filter','adapter_nr == 4')
  write(I/'events/i2c/i2c_read/enable',1);write(I/'events/i2c/i2c_result/enable',1);i2c_enabled=True
 fd=os.open('/dev/input/'+event.name,os.O_RDONLY|os.O_NONBLOCK|os.O_CLOEXEC)
 initial_version=Path('/sys/module/f8_gsl_shuping/srcversion').read_text().strip()
 fcntl.ioctl(fd,0x400445a0,struct.pack('i',1));fmt=struct.Struct('llHHi');assert fmt.size==24
 state.update(phase='waiting_for_touch');save();deadline=time.monotonic()+180;pending=b''
 while time.monotonic()<deadline:
  ready,_,_=select.select([fd],[],[],.1)
  if not ready:continue
  pending+=os.read(fd,fmt.size*256)
  while len(pending)>=fmt.size:
   sec,usec,kind,code,value=fmt.unpack_from(pending);pending=pending[fmt.size:]
   if kind==3 and code==0x2f:slot=value
   elif kind==3 and code==0x39:
    if value<0:slots.discard(slot)
    else:slots.add(slot)
   elif kind==0 and code==3:drops+=1
   elif kind==0 and code==0:
    if start is None and slots and flag.exists():
     start=time.monotonic();deadline=start+20;write(I/'tracing_on',1)
     state.update(phase='capturing',start_monotonic=start,duration_seconds=20);save()
    if start is not None:frames.append({'t':sec+usec/1e6,'contacts':len(slots)})
 assert start is not None,'No touch within the bounded wait'
 write(I/'tracing_on',0);trace=(I/'trace').read_text();(W/'irq-trace.txt').write_text(trace)
 assert Path('/sys/module/f8_gsl_shuping/srcversion').read_text().strip()==initial_version,'Driver changed during capture'
 times=[float(m[1]) for l in trace.splitlines() if (m:=re.search(r'\s(\d+\.\d+):\s+irq_handler_entry:',l))]
 def stats(ts):
  gaps=[(y-x)*1000 for x,y in zip(ts,ts[1:]) if y>x]
  intervals=[v for v in gaps if v<100]
  return {'records':len(ts),'intervals_under_100ms':len(intervals),'median_ms':statistics.median(intervals) if intervals else None,'median_hz':1000/statistics.median(intervals) if intervals else None,'intervals_7_to_10ms':sum(7<=v<=10 for v in intervals),'intervals_13_to_17ms':sum(13<=v<=17 for v in intervals),'gaps_over_100ms':sum(v>=100 for v in gaps)}
 result={'round':a.round,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'srcversion':Path('/sys/module/f8_gsl_shuping/srcversion').read_text().strip(),'start_monotonic':start,'duration_seconds':20,'irq':stats(times),'evdev':stats([f['t'] for f in frames]),'syn_dropped':drops,'max_contacts':max([f['contacts'] for f in frames],default=0),'irq_timestamps':times,'frames':frames,'device_modified':False}
 result['contact_release_transitions']=sum(a['contacts']>b['contacts'] for a,b in zip(frames,frames[1:]))
 result['zero_contact_frames']=sum(f['contacts']==0 for f in frames)
 read_started=None;read_ms=[]
 for line in trace.splitlines():
  m=re.search(r'\s(\d+\.\d+):\s+(i2c_read|i2c_result):',line)
  if not m:continue
  if m[2]=='i2c_read':read_started=float(m[1])
  elif read_started is not None:
   read_ms.append((float(m[1])-read_started)*1000);read_started=None
 result['i2c_44byte_read']={'trace_enabled':i2c_enabled,'samples':len(read_ms),'median_ms':statistics.median(read_ms) if read_ms else None,'max_ms':max(read_ms) if read_ms else None,'payload_captured':False}
 (W/'result.json').write_text(json.dumps(result,indent=2)+'\n');state.update(phase='finished',summary={k:result[k] for k in ['srcversion','irq','evdev','syn_dropped','max_contacts']});save()
except BaseException as e:
 state.update(phase='failed',error=str(e));save();raise
finally:
 if fd is not None:os.close(fd)
 if created:
  write(I/'tracing_on',0);write(I/'events/irq/irq_handler_entry/enable',0)
  for name in ['i2c_read','i2c_result']:
   if (I/('events/i2c/'+name+'/enable')).exists():write(I/('events/i2c/'+name+'/enable'),0)
  I.rmdir()
