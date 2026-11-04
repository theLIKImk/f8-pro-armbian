"""Strict reader/writer for the archived three-file Rockchip v0 resource image."""
import hashlib,struct
def parse(data):
    assert data[:4]==b'RSCE' and data[4:8]==b'\0'*4 and data[8:11]==b'\1\1\1'
    count=struct.unpack_from('<I',data,12)[0];assert count==3
    files={};ranges=[]
    for i in range(count):
        entry=data[512+i*512:1024+i*512];assert len(entry)==512 and entry[:4]==b'ENTR'
        name=entry[4:224].split(b'\0',1)[0].decode();assert name not in files
        assert name in ['rk-kernel.dtb','logo.bmp','logo_kernel.bmp']
        n,pos,size=struct.unpack_from('<3I',entry,256)
        assert n==20 and pos>=count+1 and size>0 and pos*512+size<=len(data)
        content=data[pos*512:pos*512+size]
        assert hashlib.sha1(content).digest()==entry[224:244]
        ranges.append((pos*512,pos*512+size));files[name]=content
    ranges.sort();assert all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:]))
    return files
def replace_dtb(data,dtb):
    original=parse(data);assert dtb[:4]==bytes.fromhex('d00dfeed')
    result=bytearray(data[:2048]);offset=4
    for i in range(3):
        entry=bytearray(data[512+i*512:1024+i*512]);name=entry[4:224].split(b'\0',1)[0].decode()
        content=dtb if name=='rk-kernel.dtb' else original[name]
        entry[224:256]=hashlib.sha1(content).digest()+b'\0'*12
        struct.pack_into('<3I',entry,256,20,offset,len(content))
        result[512+i*512:1024+i*512]=entry
        result.extend(content);result.extend(b'\0'*((-len(result))%512));offset=len(result)//512
    checked=parse(result)
    assert checked['rk-kernel.dtb']==dtb
    for name in ['logo.bmp','logo_kernel.bmp']:assert checked[name]==original[name]
    return bytes(result)
