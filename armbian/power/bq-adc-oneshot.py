"""Bounded BQ25890 single ADC strobe. No charger-policy or reset writes."""
import ctypes as C
import fcntl
import json
import os
from pathlib import Path
import struct
import time

class Msg(C.Structure):
    _fields_=[('addr',C.c_uint16),('flags',C.c_uint16),('len',C.c_uint16),('buf',C.POINTER(C.c_uint8))]
class Transfer(C.Structure):
    _fields_=[('msgs',C.POINTER(Msg)),('nmsgs',C.c_uint32)]

def transaction(fd,messages,ioctl=None):
    request=Transfer(messages,len(messages))
    if ioctl is None:
        result=C.CDLL(None,use_errno=True).ioctl(fd,C.c_ulong(0x0707),C.byref(request))
        if result<0:raise OSError(C.get_errno(),os.strerror(C.get_errno()))
    else:result=ioctl(fd,0x0707,request)
    if result!=len(messages):raise OSError('Incomplete I2C transaction')

class Bus:
    def __init__(self,fd,ioctl=None):self.fd=fd;self.ioctl=ioctl
    def read(self,register,count):
        if (register,count) not in [(0,12),(13,8),(2,1),(20,1)]:raise ValueError('Read not whitelisted')
        pointer=(C.c_uint8*1)(register);data=(C.c_uint8*count)()
        messages=(Msg*2)(Msg(0x6a,0,1,pointer),Msg(0x6a,1,count,data))
        transaction(self.fd,messages,self.ioctl);return bytes(data)
    def snapshot(self):
        raw={i:v for i,v in enumerate(self.read(0,12))}
        raw.update({13+i:v for i,v in enumerate(self.read(13,8))});return raw
    def start_once(self,old):
        if old&0xc2:raise ValueError('ADC continuous/busy or DPDM detection active')
        data=(C.c_uint8*2)(2,old|0x80)
        messages=(Msg*1)(Msg(0x6a,0,2,data))
        transaction(self.fd,messages,self.ioctl)

def measure(bus,clock=time.monotonic,sleep=time.sleep):
    report={'scope':'BQ25890 one-shot ADC; no charging-policy change',
      'source':'https://www.ti.com/lit/gpn/bq25890','charging_policy_writes':0,
      'adc_start_strobes':0,'fault_reg_0c_skipped':True,'complete':False}
    try:
        pn=(bus.read(20,1)[0]>>3)&7
        if pn!=3:raise RuntimeError('Unexpected part number')
        before=bus.snapshot();report['before_raw']={hex(k):v for k,v in before.items()}
        report['identity']={'part_code':pn,'revision':before[20]&3,'silicon_manufacturer_verified':False}
        control=before[2]
        if control&0xc2:raise RuntimeError('Busy/continuous ADC or DPDM; leave untouched')
        if bus.read(2,1)[0]!=control:raise RuntimeError('Control changed; leave untouched')
        bus.start_once(control);report['adc_start_strobes']=1
        started=clock();deadline=started+2
        busy_seen=False
        while True:
            latest=bus.read(2,1)[0]
            if not latest&0x80:break
            busy_seen=True
            if clock()>=deadline:raise RuntimeError('ADC did not auto-clear; no forced reset or restore')
            sleep(0.1)
        after=bus.snapshot();report['elapsed_seconds']=clock()-started
        report['conversion_completed_monotonic']=clock()
        report['after_raw']={hex(k):v for k,v in after.items()}
        keys=[0,1,2,3,4,5,6,7,8,9,10,13]
        report['configuration_differences']={hex(k):[before[k],after[k]] for k in keys if before[k]!=after[k]}
        report['adc_strobe_auto_cleared']=not bool(after[2]&0x80)
        report['adc_busy_observed']=busy_seen
        report['conversion_handshake_verified']=busy_seen and not bool(after[2]&0x80)
        report['configuration_unchanged']=not report['configuration_differences']
        report['measurement']={
          'battery_uv':2304000+(after[14]&127)*20000,
          'vbus_good':bool(after[17]&128),
          'vbus_uv':2600000+(after[17]&127)*100000 if after[17]&128 else None,
          'battery_charge_adc_ma':(after[18]&127)*50,
          'charge_current_raw_code':after[18]&127,
          'battery_current_channel_validated':False,'actual_battery_current_ma':None,
          'linux_current_now_ua_assuming_bq25890':-(after[18]&127)*50000,
          'thermal_regulation_flag':bool(after[14]&128),'thermistor_ratio_raw':after[16]&127,
          'charging_status_code':(after[11]>>3)&3,'input_dpm':bool(after[19]&64),
          'voltage_dpm':bool(after[19]&128),
          'note':'Scaled raw code under BQ25890 register-map assumption; current channel unvalidated; zero code does not prove actual zero current; not USB input current'}
        report['complete']=report['configuration_unchanged']
    except Exception as error:report['error']=str(error)
    return report

def main():
    report={'complete':False}
    try:
        adapter=Path('/sys/bus/i2c/devices/i2c-6/of_node').resolve(strict=True)
        if adapter.name!='i2c@fec80000':raise RuntimeError('Unexpected bus controller')
        pins=struct.unpack('>8I',Path('/proc/device-tree/pinctrl/i2c6/i2c6m3-xfer/rockchip,pins').read_bytes())
        if sorted([pins[:3],pins[4:7]])!=[(4,8,9),(4,9,9)]:raise RuntimeError('Unexpected pinmux')
        if (adapter/'charger@6a/status').read_bytes()!=b'disabled\0':raise RuntimeError('Standard charger node enabled')
        if Path('/sys/bus/i2c/devices/6-006a/driver').exists():raise RuntimeError('Charger owned by kernel driver')
        fd=os.open('/dev/i2c-6',os.O_RDWR|os.O_CLOEXEC)
        try:
            with Path('/run/f8/bq-adc.lock').open('a') as lock:
                fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                fcntl.ioctl(fd,0x0703,0x6a)
                report=measure(Bus(fd))
        finally:os.close(fd)
    except Exception as error:report['error']=str(error)
    report['boot_id']=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    report['uptime_seconds']=float(Path('/proc/uptime').read_text().split()[0])
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
