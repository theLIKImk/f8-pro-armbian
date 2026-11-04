"""Verify allowed I2C wire messages and selected TI decoding without hardware."""
import importlib.util
from pathlib import Path
P=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('power',P/'armbian/official-graphics/power-readonly.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
seen=[]
def ioctl(fd,command,transfer):
    assert command==0x0707 and transfer.nmsgs==2
    pointer,read=transfer.msgs[0],transfer.msgs[1]
    assert pointer.flags==0 and pointer.len==1 and read.flags==1 and pointer.addr==read.addr
    register=pointer.buf[0]
    assert pointer.addr in [0x62,0x6a]
    assert not(pointer.addr==0x6a and register<=12<register+read.len)
    seen.append((pointer.addr,register,read.len))
    for i in range(read.len):read.buf[i]=(register+i)&255
    return 2
for address,regions in m.REGIONS.items():
    for start,count in regions:
        assert m.read_region(-1,address,start,count,ioctl)==bytes(range(start,start+count))
for address,register,count in [(0x6a,12,1),(0x22,0,1),(0x62,0x0a,2)]:
    try:m.read_region(-1,address,register,count,ioctl)
    except ValueError:pass
    else:raise AssertionError('Unlisted transaction accepted')
raw={i:0 for i in range(21)};raw.update({0:8,4:39,5:0,6:35<<2,0x14:3<<3})
d=m.decode_bq(raw)
assert d['input_limit_ua']==500000 and d['charge_current_setting_ua']==2496000
assert d['regulation_voltage_uv']==4400000 and d['termination_setting_ua']==64000
raw[0x14]=7<<3
assert 'regulation_voltage_uv' not in m.decode_bq(raw)
print('PASS: 7 whitelisted read regions, no register-value write, fault register skipped; bounds and variant decoding checked')
