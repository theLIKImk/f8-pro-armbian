"""Decode candidate Android sensor_t descriptors from ELF64, resolving local RELA pointers."""
from pathlib import Path
import struct,json,math
P=Path(__file__).resolve().parents[1];O=P/'analysis/armbian/android-sensor-audit-20261103'
f=O/'vendor/lib64/hw/sensors.rk30board.so';b=f.read_bytes();assert b[:6]==b'\x7fELF\x02\x01'
phoff,shoff=struct.unpack_from('<QQ',b,32);phsize,phnum,shsize,shnum=struct.unpack_from('<4H',b,54)
loads=[]
for i in range(phnum):
 typ,flags,off,va,pa,fs,ms,align=struct.unpack_from('<II6Q',b,phoff+i*phsize)
 if typ==1:loads.append((va,va+fs,off,flags))
def offset(va,n=1):
 for a,z,o,fl in loads:
  if a<=va and va+n<=z:return o+va-a
 return None
rel={}
for i in range(shnum):
 sh=struct.unpack_from('<II4QII2Q',b,shoff+i*shsize);typ=sh[1];off=sh[4];size=sh[5];es=sh[9]
 if typ==4:
  for j in range(off,off+size,es):
   va,info,addend=struct.unpack_from('<QQq',b,j)
   if info&0xffffffff==1027:rel[va]=addend
# Android uses packed RELA and RELR rather than a plain .rela.dyn table.
for i in range(shnum):
 sh=struct.unpack_from('<II4QII2Q',b,shoff+i*shsize);typ=sh[1];off=sh[4];size=sh[5]
 if typ==0x6fffff00:
  where=0
  for j in range(off,off+size,8):
   word=struct.unpack_from('<Q',b,j)[0]
   if not word&1:
    where=word;o=offset(where,8)
    if o is not None:rel[where]=struct.unpack_from('<Q',b,o)[0]
    where+=8
   else:
    for bit in range(1,64):
     if word&(1<<bit):
      va=where+(bit-1)*8;o=offset(va,8)
      if o is not None:rel[va]=struct.unpack_from('<Q',b,o)[0]
    where+=63*8
 if typ==0x60000002:
  data=b[off:off+size];assert data[:4]==b'APS2';at=[4]
  def sleb():
   value=shift=0
   while True:
    x=data[at[0]];at[0]+=1;value|=(x&127)<<shift;shift+=7
    if not x&128:break
   return value-(1<<shift) if x&64 else value
  count=sleb();va=sleb();addend=0;done=0
  while done<count:
   n=sleb();flags=sleb();delta=sleb() if flags&2 else 0;info=sleb() if flags&1 else 0
   ad=sleb() if flags&8 and flags&4 else 0
   for _ in range(n):
    va+=delta if flags&2 else sleb()
    ri=info if flags&1 else sleb()
    if flags&8:addend+=ad if flags&4 else sleb()
    else:addend=0
    if ri&0xffffffff==1027:rel[va]=addend
   done+=n
def pointer(va):
 if va in rel:return rel[va]
 o=offset(va,8);return struct.unpack_from('<Q',b,o)[0] if o is not None else 0
def string(va):
 o=offset(va)
 if o is None:return None
 raw=b[o:o+240].split(b'\0')[0]
 if not raw or any(c<32 or c>126 for c in raw):return None
 return raw.decode()
types={1:'accelerometer',2:'magnetic_field',3:'orientation',4:'gyroscope',5:'light',6:'pressure',8:'proximity',9:'gravity',10:'linear_acceleration',11:'rotation_vector',14:'magnetic_field_uncalibrated',15:'game_rotation_vector',16:'gyroscope_uncalibrated',17:'significant_motion',18:'step_detector',19:'step_counter',20:'geomagnetic_rotation_vector',22:'tilt_detector',23:'wake_gesture',24:'glance_gesture',25:'pick_up_gesture',27:'device_orientation',28:'pose_6dof',30:'motion_detect',29:'stationary_detect'}
result=[]
for va in sorted(rel):
 name=string(pointer(va));vendor=string(pointer(va+8));off=offset(va,104)
 if not name or not vendor or off is None:continue
 version,handle,typ=struct.unpack_from('<3i',b,off+16)
 if typ not in types or not 0<version<100 or not 0<=handle<1000:continue
 maxrange,res,power=struct.unpack_from('<3f',b,off+28);mindelay,fifoRes,fifoMax=struct.unpack_from('<iII',b,off+40)
 st=string(pointer(va+56));permission=string(pointer(va+64));maxdelay,flags=struct.unpack_from('<qQ',b,off+72)
 if not st or not st.startswith('android.sensor.') or any(not math.isfinite(x) for x in [maxrange,res,power]):continue
 result.append({'struct_va':hex(va),'name':name,'vendor':vendor,'version':version,'handle':handle,'type_id':typ,'type':types[typ],'string_type':st,'max_range':maxrange,'resolution':res,'power_mA':power,'min_delay_us':mindelay,'max_delay_us':maxdelay,'fifo_reserved':fifoRes,'fifo_max':fifoMax,'flags':flags,'required_permission':permission})
(O/'hal-sensor-descriptors.json').write_text(json.dumps({'source':str(f.relative_to(P)),'entries':result,'abi':'Android 12 LP64 sensor_t: 104 bytes, 64-bit maxDelay and flags','note':'Static HAL descriptors; runtime availability still depends on driver initialization.'},indent=2)+'\n')
print(json.dumps(result,indent=2))
