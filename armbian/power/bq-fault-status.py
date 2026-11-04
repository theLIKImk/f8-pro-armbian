"""Explicit latched/live fault read. First read is preserved before second read."""
import ctypes as C
import fcntl
import json
import os
from pathlib import Path
import time
class Msg(C.Structure):
    _fields_=[('addr',C.c_uint16),('flags',C.c_uint16),('len',C.c_uint16),('buf',C.POINTER(C.c_uint8))]
class Transfer(C.Structure):
    _fields_=[('msgs',C.POINTER(Msg)),('nmsgs',C.c_uint32)]
def read(fd,register):
    if register not in [0x0b,0x0c,0x14]:raise ValueError('Register not allowed')
    pointer=(C.c_uint8*1)(register);value=(C.c_uint8*1)()
    messages=(Msg*2)(Msg(0x6a,0,1,pointer),Msg(0x6a,1,1,value))
    req=Transfer(messages,2)
    result=C.CDLL(None,use_errno=True).ioctl(fd,C.c_ulong(0x0707),C.byref(req))
    if result!=2:raise OSError(C.get_errno(),'Fault read failed')
    return value[0]
def decode(value):
    ntc=value&7
    return {'raw':value,'watchdog_fault':bool(value&128),'boost_fault':bool(value&64),
      'charge_fault_code':(value>>4)&3,'battery_overvoltage_fault':bool(value&8),
      'ntc_code':ntc,'ntc_buck_interpretation':{0:'normal',2:'warm',3:'cool',5:'cold',6:'hot'}.get(ntc,'reserved')}
def main():
    report={'scope':'Explicit read-to-clear fault latch and current fault status','register_value_writes':0}
    path=Path('/run/f8/bq-fault-latched-first-01.json')
    try:
        node=Path('/sys/bus/i2c/devices/i2c-6/of_node').resolve(strict=True)
        if node.name!='i2c@fec80000':raise RuntimeError('Unexpected controller')
        if (node/'charger@6a/status').read_bytes()!=b'disabled\0':raise RuntimeError('Kernel charger enabled')
        if Path('/sys/bus/i2c/devices/6-006a/driver').exists():raise RuntimeError('Charger driver bound')
        with path.open('x') as saved:
            fd=os.open('/dev/i2c-6',os.O_RDWR|os.O_CLOEXEC)
            try:
                fcntl.ioctl(fd,0x0703,0x6a)
                if (read(fd,0x14)>>3)&7!=3:raise RuntimeError('Unexpected part')
                report['status_before']=read(fd,0x0b)
                report['latched_first']=decode(read(fd,0x0c))
                saved.write(json.dumps(report)+'\n');saved.flush();os.fsync(saved.fileno())
                time.sleep(0.05)
                report['current_second']=decode(read(fd,0x0c))
                report['status_after']=read(fd,0x0b)
                report['complete']=True
            finally:os.close(fd)
    except Exception as error:report.update(complete=False,error=str(error))
    report['boot_id']=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    report['uptime_seconds']=float(Path('/proc/uptime').read_text().split()[0])
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
