"""Bounded, non-grabbing capture of the F8 touchscreen only; never read keyboards."""
import argparse
from collections import deque
import fcntl
import json
import os
from pathlib import Path
import select
import struct
import time

parser=argparse.ArgumentParser()
parser.add_argument('--seconds',type=int,default=110)
parser.add_argument('--discovery-seconds',type=int,default=15)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();assert 0<=args.seconds<=120
assert 0<=args.discovery_seconds<=15
result={'driver_name':'f8-gsl-shuping','device_found':False,'event_count':0,'syn_frames':0,
        'max_active_contacts':0,'press_count':0,'release_count':0,'dropped_frames':0,
        'sample_frames':[],'last_frames':[],'observed_range':{}}
def save():
    args.output.parent.mkdir(parents=True,exist_ok=True)
    temp=args.output.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2)+'\n');temp.replace(args.output)
fd=None;started=time.monotonic()
try:
    device=None
    for attempt in range(args.discovery_seconds+1):
        for event in Path('/sys/class/input').glob('event*'):
            name=event/'device/name'
            if name.exists() and name.read_text().strip()=='f8-gsl-shuping':
                device=event;break
        if device is not None:break
        if attempt<args.discovery_seconds:time.sleep(1)
    if device is None:raise RuntimeError('F8 touch input device not found')
    fd=os.open('/dev/input/'+device.name,os.O_RDONLY|os.O_NONBLOCK|os.O_CLOEXEC)
    result.update(device_found=True,event_device=device.name)
    axes={}
    for name,code in [('slot',0x2f),('x',0x35),('y',0x36),('tracking_id',0x39)]:
        data=bytearray(24);request=(2<<30)|(24<<16)|(ord('E')<<8)|(0x40+code)
        fcntl.ioctl(fd,request,data,True)
        value,minimum,maximum,fuzz,flat,resolution=struct.unpack('6i',data)
        axes[name]={'minimum':minimum,'maximum':maximum,'resolution':resolution}
    result['axes']=axes
    driver=Path('/sys/bus/i2c/devices/4-0040/driver')
    result['bound_i2c_driver']=driver.resolve().name if driver.is_symlink() else None
    event_format=struct.Struct('llHHi');assert event_format.size==24
    slots={};slot=0;tail=deque(maxlen=10);pending=b'';last_save=0
    deadline=time.monotonic()+args.seconds
    while time.monotonic()<deadline:
        ready,_,_=select.select([fd],[],[],min(1,max(0,deadline-time.monotonic())))
        if ready:
            try:
                chunk=os.read(fd,event_format.size*128)
                if not chunk:raise RuntimeError('Touch event device closed')
                pending+=chunk
            except BlockingIOError:continue
            while len(pending)>=event_format.size:
                sec,usec,kind,code,value=event_format.unpack_from(pending);pending=pending[event_format.size:]
                result['event_count']+=1
                if kind==3:
                    if code==0x2f:slot=value
                    elif code==0x39:
                        if value<0:
                            if slot in slots:result['release_count']+=1
                            slots.pop(slot,None)
                        else:slots.setdefault(slot,{})['tracking_id']=value;result['press_count']+=1
                    elif code in [0x35,0x36]:
                        key='x' if code==0x35 else 'y';slots.setdefault(slot,{})[key]=value
                        limits=result['observed_range'].setdefault(key,{'minimum':value,'maximum':value})
                        limits['minimum']=min(limits['minimum'],value);limits['maximum']=max(limits['maximum'],value)
                elif kind==0 and code==3:
                    result['dropped_frames']+=1;slots.clear()
                elif kind==0 and code==0:
                    points=[dict(slot=n,**v) for n,v in sorted(slots.items()) if 'tracking_id' in v]
                    result['syn_frames']+=1;result['max_active_contacts']=max(result['max_active_contacts'],len(points))
                    frame={'elapsed_seconds':round(time.monotonic()-started,3),'points':points}
                    if len(result['sample_frames'])<200:result['sample_frames'].append(frame)
                    tail.append(frame)
        if time.monotonic()-last_save>=2:
            result['last_frames']=list(tail);result['capture_elapsed_seconds']=round(time.monotonic()-started,2)
            save();last_save=time.monotonic()
    result['capture_complete']=True;result['last_frames']=list(tail)
except Exception as error:
    result['error']=str(error);result['capture_complete']=False
finally:
    if fd is not None:os.close(fd)
result['capture_elapsed_seconds']=round(time.monotonic()-started,2)
save()
print(json.dumps({k:v for k,v in result.items() if k not in ['sample_frames','last_frames']},indent=2))
raise SystemExit(0 if result['device_found'] else 1)
