"""Compare burst/byte reads under bounded continuous ADC; restore original mode."""
import ctypes as C
import fcntl
import json
import os
from pathlib import Path
import signal
import struct
import time

class Msg(C.Structure):
    _fields_=[('addr',C.c_uint16),('flags',C.c_uint16),('len',C.c_uint16),('buf',C.POINTER(C.c_uint8))]
class Transfer(C.Structure):
    _fields_=[('msgs',C.POINTER(Msg)),('nmsgs',C.c_uint32)]
class Bus:
    def __init__(self,fd,ioctl=None):self.fd=fd;self.ioctl=ioctl
    def transfer(self,messages):
        req=Transfer(messages,len(messages))
        if self.ioctl:result=self.ioctl(self.fd,0x0707,req)
        else:
            result=C.CDLL(None,use_errno=True).ioctl(self.fd,C.c_ulong(0x0707),C.byref(req))
            if result<0:raise OSError(C.get_errno(),os.strerror(C.get_errno()))
        if result!=len(messages):raise OSError('Incomplete I2C transaction')
    def read(self,register,count=1):
        if not ((count==1 and 0<=register<=20 and register!=12) or (register,count) in [(0,12),(13,8)]):
            raise ValueError('Read outside audit whitelist')
        pointer=(C.c_uint8*1)(register);data=(C.c_uint8*count)()
        self.transfer((Msg*2)(Msg(0x6a,0,1,pointer),Msg(0x6a,1,count,data)))
        return bytes(data)
    def adc_mode(self,current,new):
        if (current&0x3f)!=(new&0x3f) or new&0x80 or current&2:
            raise ValueError('Only ADC continuous-mode change allowed; no start/DPDM strobe')
        data=(C.c_uint8*2)(2,new)
        self.transfer((Msg*1)(Msg(0x6a,0,2,data)))
    def snapshot(self):
        raw={i:v for i,v in enumerate(self.read(0,12))}
        raw.update({13+i:v for i,v in enumerate(self.read(13,8))});return raw

def audit(bus,sleep=time.sleep):
    report={'scope':'ADC sampling audit, temporary continuous mode only','charging_policy_writes':0,
        'samples':[],'complete':False,'restored':False,'mode_enable_attempted':False}
    before=bus.snapshot();report['before_raw']={hex(k):v for k,v in before.items()}
    old=before[2]
    if ((before[20]>>3)&7)!=3 or old&0xc2 or not before[11]&4:
        report['error']='Unexpected PN, ADC/DPDM busy or no input; untouched';return report
    report['identity']={'part_code':(before[20]>>3)&7,'revision':before[20]&3,
        'ti_documented_revision':1,'silicon_manufacturer_confirmed':False}
    try:
        if bus.read(2)[0]!=old:raise RuntimeError('Control changed before audit')
        report['mode_enable_attempted']=True
        bus.adc_mode(old,old|0x40)
        sleep(1.3)
        for index in range(5):
            ctrl=bus.read(2)[0]
            if ctrl&0x3f!=old&0x3f or not ctrl&0x40:raise RuntimeError('Unexpected ADC control state')
            pre=bus.read(18)[0]
            block=bus.read(13,8)
            single={register:bus.read(register)[0] for register in range(13,21)}
            post=bus.read(18)[0]
            cow=json.loads(Path('/run/f8/power-current.json').read_text()) if Path('/run/f8/power-current.json').exists() else None
            report['samples'].append({'index':index,'control':ctrl,'burst':{hex(13+i):v for i,v in enumerate(block)},
              'single':{hex(k):v for k,v in single.items()},'current_raw_bracket':[pre,block[5],post],
              'current_raw_single':single[18],'charge_adc_ma':(single[18]&127)*50,
              'actual_battery_current_ma':None,'battery_current_channel_validated':False,
              'battery_adc_uv':2304000+(single[14]&127)*20000,
              'vbus_good':bool(single[17]&128),'vbus_adc_uv':2600000+(single[17]&127)*100000 if single[17]&128 else None,
              'cw':cow['devices']['0x62'].get('decoded') if cow and '0x62' in cow.get('devices',{}) else None})
            if index<4:sleep(1.2)
    except Exception as error:report['error']=str(error)
    finally:
        if report['mode_enable_attempted']:
            try:
                ctrl=bus.read(2)[0]
                bus.adc_mode(ctrl,ctrl&0x3f)
                for count in range(15):
                    if not bus.read(2)[0]&0xc0:break
                    sleep(0.1)
                after=bus.snapshot();report['after_raw']={hex(k):v for k,v in after.items()}
                report['restored']=after[2]==old
                keys=[0,1,2,3,4,5,6,7,8,9,10,13]
                report['configuration_differences']={hex(k):[before[k],after[k]] for k in keys if before[k]!=after[k]}
            except Exception as error:report['restore_error']=str(error)
    report['complete']=len(report['samples'])==5 and report['restored'] and not report.get('configuration_differences') and 'error' not in report
    return report

def main():
    def interrupted(*args):raise RuntimeError('Signal received; restore ADC mode')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGHUP,interrupted)
    report={'complete':False}
    try:
        node=Path('/sys/bus/i2c/devices/i2c-6/of_node').resolve(strict=True)
        if node.name!='i2c@fec80000':raise RuntimeError('Wrong controller')
        pins=struct.unpack('>8I',Path('/proc/device-tree/pinctrl/i2c6/i2c6m3-xfer/rockchip,pins').read_bytes())
        if sorted([pins[:3],pins[4:7]])!=[(4,8,9),(4,9,9)]:raise RuntimeError('Wrong pins')
        if (node/'charger@6a/status').read_bytes()!=b'disabled\0' or Path('/sys/bus/i2c/devices/6-006a/driver').exists():
            raise RuntimeError('Standard charger is active')
        fd=os.open('/dev/i2c-6',os.O_RDWR|os.O_CLOEXEC)
        try:
            with Path('/run/f8/bq-adc.lock').open('a') as lock:
                fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                fcntl.ioctl(fd,0x0703,0x6a)
                report=audit(Bus(fd))
        finally:os.close(fd)
    except Exception as error:report['error']=str(error)
    report['boot_id']=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    report['uptime_seconds']=float(Path('/proc/uptime').read_text().split()[0])
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
