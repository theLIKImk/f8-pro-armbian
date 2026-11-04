"""F8 G5: fixed-address, register-read-only BQ/CW snapshot. No charger control."""
import argparse
import ctypes as C
import fcntl
import hashlib
import json
import os
from pathlib import Path
import struct
import time

BUS=6
EXPECTED_PINS=[4,8,9,4,9,9]
REGIONS={0x6a:((0x00,12),(0x0d,8)),
         0x62:((0x00,1),(0x02,4),(0x08,1),(0x0a,1),(0x10,64))}
class Msg(C.Structure):
    _fields_=[('addr',C.c_uint16),('flags',C.c_uint16),('len',C.c_uint16),('buf',C.POINTER(C.c_uint8))]
class Transfer(C.Structure):
    _fields_=[('msgs',C.POINTER(Msg)),('nmsgs',C.c_uint32)]

def read_region(fd,address,register,count,ioctl=None):
    if (register,count) not in REGIONS.get(address,()):
        raise ValueError('Register region not allowed')
    # Write message sets the register pointer only: exactly one byte, no value.
    pointer=(C.c_uint8*1)(register);data=(C.c_uint8*count)()
    messages=(Msg*2)(Msg(address,0,1,pointer),Msg(address,1,count,data))
    transfer=Transfer(messages,2)
    if ioctl is None:
        libc=C.CDLL(None,use_errno=True)
        result=libc.ioctl(fd,C.c_ulong(0x0707),C.byref(transfer))
        if result<0:raise OSError(C.get_errno(),os.strerror(C.get_errno()))
    else:result=ioctl(fd,0x0707,transfer)
    if result!=2:raise OSError('Incomplete I2C transfer: '+str(result))
    return bytes(data)

def decode_bq(raw):
    pn=(raw[0x14]>>3)&7
    result={'part_number_code':pn,'bq25890_part_code_match':pn==3,
            'revision_code':raw[0x14]&3,'silicon_manufacturer_verified':False,
            'adc_refreshed_by_this_reader':False,'battery_current_channel_validated':False}
    if pn!=3:
        result['note']='Raw data only: unconfirmed chip variant; no BQ25890 scaling applied'
        return result
    result.update(input_limit_ua=100000+(raw[0]&63)*50000,
      charge_current_setting_ua=(raw[4]&127)*64000,
      regulation_voltage_uv=3840000+(raw[6]>>2)*16000,
      termination_setting_ua=64000+(raw[5]&15)*64000,
      charge_enabled=bool(raw[3]&16),otg_enabled=bool(raw[3]&32),
      high_impedance=bool(raw[0]&128),watchdog_code=(raw[7]>>4)&3,
      safety_timer_enabled=bool(raw[7]&8),vbus_status=(raw[11]>>5)&7,
      charging_status=(raw[11]>>3)&3,power_good=bool(raw[11]&4),
      adc_conversion_start=bool(raw[2]&128),adc_continuous=bool(raw[2]&64),
      battery_adc_uv=2304000+(raw[14]&127)*20000,
      adc_note='Existing sample only; no conversion triggered, freshness unverified')
    return result

def decode_cw(raw,profile):
    word=(raw[2]<<8)|raw[3]
    stored=bytes(raw[x] for x in range(0x10,0x50))
    return {'version_raw':raw[0],'mode_raw':raw[10],'sleep_mode':(raw[10]&0xc0)==0xc0,
      'soc_raw_percent':raw[4]+raw[5]/256,'soc_in_range':raw[4]<=100,
      'voltage_raw_word':word,'voltage_mv_reference_formula':word*312//1024,
      'voltage_note':'Uses local CW2015 source formula; single read, not averaged; no series-cell multiplier assumed',
      'profile_sha256':hashlib.sha256(stored).hexdigest(),'profile_equals_factory':stored==profile}

def save(path,report):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(report,indent=2)+'\n');temporary.replace(path)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    report={'scope':'G5 passive register snapshot; not charging acceptance','monotonic_seconds':time.monotonic(),
      'register_value_writes':0,'fault_reg_0c_skipped':True,'devices':{},'complete':False}
    save(output,report)
    try:
        adapter=Path('/sys/bus/i2c/devices/i2c-6')
        node=(adapter/'of_node').resolve(strict=True)
        if node.name!='i2c@fec80000':raise RuntimeError('Unexpected I2C6 physical controller')
        group=Path('/proc/device-tree/pinctrl/i2c6/i2c6m3-xfer')
        pins=struct.unpack('>8I',(group/'rockchip,pins').read_bytes())
        if sorted([pins[:3],pins[4:7]])!=[(4,8,9),(4,9,9)]:raise RuntimeError('Unexpected I2C6 pins')
        profile=(node/'cw2015@62/cellwise,battery-profile').read_bytes()
        if len(profile)!=64:raise RuntimeError('Unexpected factory profile length')
        report['physical_bus_verified']=str(node)
        # Standard client drivers must remain disabled. No force ioctl.
        for address,name in [(0x6a,'charger@6a'),(0x62,'cw2015@62')]:
            if (node/name/'status').read_bytes()!=b'disabled\0':raise RuntimeError('Power node is enabled')
            if (Path('/sys/bus/i2c/devices')/('6-%04x'%address)/'driver').exists():
                raise RuntimeError('Power client driver already bound')
        fd=os.open('/dev/i2c-6',os.O_RDWR|os.O_CLOEXEC)
        try:
            for address in [0x6a,0x62]:
                item={'address':hex(address),'raw':{}};report['devices'][hex(address)]=item
                try:
                    fcntl.ioctl(fd,0x0703,address) # I2C_SLAVE checks that no kernel client owns address.
                    raw={}
                    for start,count in REGIONS[address]:
                        data=read_region(fd,address,start,count)
                        raw.update({start+i:value for i,value in enumerate(data)})
                        item['raw']={hex(k):v for k,v in raw.items()};save(output,report)
                    item['decoded']=decode_bq(raw) if address==0x6a else decode_cw(raw,profile)
                    item['read_complete']=True
                except Exception as error:item['error']=str(error)
                save(output,report)
        finally:os.close(fd)
        report['complete']=all(v.get('read_complete',False) for v in report['devices'].values())
    except Exception as error:report['error']=str(error)
    save(output,report)
    return 0 if report['complete'] else 1

if __name__=='__main__':raise SystemExit(main())
