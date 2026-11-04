import ctypes,fcntl,json,os
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert not Path('/sys/bus/i2c/devices/6-006a/driver').is_symlink()
class Data(ctypes.Union):_fields_=[('byte',ctypes.c_ubyte),('block',ctypes.c_ubyte*34)]
class Request(ctypes.Structure):_fields_=[('read_write',ctypes.c_ubyte),('command',ctypes.c_ubyte),('size',ctypes.c_uint32),('data',ctypes.POINTER(Data))]
fd=os.open('/dev/i2c-6',os.O_RDWR|os.O_CLOEXEC)
try:
 fcntl.ioctl(fd,0x0703,0x6a);o={}
 for reg in [0x03,0x07,0x0a,0x0b,0x14]:
  d=Data();r=Request(1,reg,2,ctypes.pointer(d));fcntl.ioctl(fd,0x0720,r);o[f'0x{reg:02x}']=int(d.byte)
finally:os.close(fd)
o['otg_config_set']=bool(o['0x03']&32);o['watchdog_field']=(o['0x07']>>4)&3
o['exported_gpio']=[p.name for p in Path('/sys/class/gpio').glob('gpio[0-9]*')]
p=Path('/sys/firmware/devicetree/base/i2c@fec80000/charger@6a/otg-mode-en-gpios')
if p.exists():
 import struct
 o['otg_gpio_cells']=list(struct.unpack('>'+str(len(p.read_bytes())//4)+'I',p.read_bytes()))
o['register_writes_performed']=False
print(json.dumps(o,indent=2))
