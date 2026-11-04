"""Read constant algorithm version IDs from candidate, stock module and old Image."""
import hashlib
import json
from pathlib import Path
import struct
P=Path(__file__).resolve().parents[1]
out=P/'armbian/touch/official-6.1.115-f8'
root=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
def function_from_module(path,name):
    data=path.read_bytes();off=struct.unpack_from('<Q',data,40)[0];size,count,strings=struct.unpack_from('<HHH',data,58)
    sections=[struct.unpack_from('<IIQQQQIIQQ',data,off+i*size) for i in range(count)]
    table=next(s for s in sections if s[1]==2);ns=sections[table[6]];names=data[ns[4]:ns[4]+ns[5]]
    for pos in range(table[4],table[4]+table[5],table[9]):
        n,info,other,index,value,length=struct.unpack_from('<IBBHQQ',data,pos)
        if names[n:].split(b'\0',1)[0].decode()==name:
            sec=sections[index];return data[sec[4]+value:sec[4]+value+length]
    raise AssertionError(name)
def version(code):
    value=None
    for index in range(0,min(len(code),64),4):
        word=struct.unpack_from('<I',code,index)[0]
        if word in [0xd503245f,0xd503201f,0xd503233f,0xd50323bf,
                    0xa9bf7bfd,0xa8c17bfd,0x910003fd]:continue
        if value is None and (word&0xfc000000==0x94000000 or word==0xaa1e03e0):continue
        if word&0x7f80001f==0x52800000:
            value=((word>>5)&0xffff)<<(((word>>21)&3)*16)
        elif word&0x7f80001f==0x72800000:
            assert value is not None
            shift=((word>>21)&3)*16
            value=(value&~(0xffff<<shift))|(((word>>5)&0xffff)<<shift)
        elif word in [0xd65f03c0,0xd65f0bff]:
            assert value is not None;return hex(value)
        else:raise AssertionError(f'Unexpected version instruction {word:08x}')
    raise AssertionError('No constant version return')
records=[]
for name,path in [('new_f8_module',out/'f8_gsl_shuping.ko'),
                  ('official_stock_module',root/'usr/lib/modules/6.1.115-vendor-rk35xx/kernel/drivers/input/touchscreen/gsl3673-800x1280.ko')]:
    code=function_from_module(path,'gsl_version_id')
    records.append({'source':name,'version_id':version(code),'function_sha256':hashlib.sha256(code).hexdigest()})
symbols=json.loads((P/'analysis/armbian/touch-static/all-symbols.json').read_text())
old=(P/'vendor/ubuntu-5.10.160/boot-assets/Image').read_bytes()
assert hashlib.sha256(old).hexdigest()=='90d648c1e4e47ce6b4a83415694fa9b4a7283465fa3749297d2078abb20bffa2'
for symbol in symbols:
    if symbol['name']=='gsl_version_id':
        offset=symbol['file_offset'];code=old[offset:offset+64]
        records.append({'source':'old_factory_Image','file_offset':offset,'version_id':version(code)})
assert any(r['source']=='old_factory_Image' for r in records)
result={'scope':'Static constant version ID comparison, not full algorithm equivalence or hardware compatibility',
        'records':records,'version_ids_equal':len({r['version_id'] for r in records})==1,
        'full_algorithm_equivalence_proven':False,'touch_hardware_tested':False}
(out/'algorithm-version-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
