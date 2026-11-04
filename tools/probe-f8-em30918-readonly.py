import os,ctypes,fcntl,json
from pathlib import Path
assert os.geteuid()==0 and not Path('/sys/bus/i2c/devices/3-0024').exists()
class Msg(ctypes.Structure):_fields_=[('addr',ctypes.c_uint16),('flags',ctypes.c_uint16),('len',ctypes.c_uint16),('buf',ctypes.c_void_p)]
class Transfer(ctypes.Structure):_fields_=[('msgs',ctypes.POINTER(Msg)),('nmsgs',ctypes.c_uint32)]
fd=os.open('/dev/i2c-3',os.O_RDWR);out={}
try:
 # Only reads config/data at the stock address; no reset/enable/GPIO changes.
 for reg,n in [(0x01,1),(0x08,3)]:
  w=(ctypes.c_uint8*1)(reg);r=(ctypes.c_uint8*n)();msgs=(Msg*2)(Msg(0x24,0,1,ctypes.addressof(w)),Msg(0x24,1,n,ctypes.addressof(r)));t=Transfer(msgs,2)
  try:fcntl.ioctl(fd,0x0707,t);out[hex(reg)]=list(r)
  except OSError as e:out[hex(reg)]={'errno':e.errno,'error':str(e)}
finally:os.close(fd)
print(json.dumps({'bus':3,'address':'0x24','configuration_writes':False,'reads':out}))
