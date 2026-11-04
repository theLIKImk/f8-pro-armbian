"""Find ARM64 logical-immediate placeholder-mask candidates in archived U-Boot."""
import hashlib
import json
from pathlib import Path
import struct
from inspect_images import fdt

P=Path(__file__).resolve().parents[1]
out=P/'analysis/armbian/loader-placeholder'
out.mkdir(parents=True,exist_ok=True)
container=(P/'vendor/ubuntu-5.10.160/boot-assets/uboot.img').read_bytes()
tree=fdt(container)
props=tree['/images/uboot']
position=int.from_bytes(props['data-position'],'big')
size=int.from_bytes(props['data-size'],'big')
load=int.from_bytes(props['load'],'big')
payload=container[position:position+size]
assert len(payload)==size and props['arch']==b'arm64\0' and props['compression']==b'none\0'
(out/'uboot-ANALYSIS-ONLY.bin').write_bytes(payload)
def decode_mask(instruction):
    width=64 if instruction>>31 else 32
    n=(instruction>>22)&1
    imms=(instruction>>10)&63
    immr=(instruction>>16)&63
    if width==32 and n:return None
    length=((n<<6)|((~imms)&63)).bit_length()-1
    if length<1:return None
    levels=(1<<length)-1
    s=imms&levels;r=immr&levels
    if s==levels:return None
    bits=1<<length
    element=(1<<(s+1))-1
    element=((element>>r)|(element<<(bits-r)))&((1<<bits)-1)
    return sum(element<<shift for shift in range(0,width,bits))
candidates=[]
for offset in range(0,len(payload)-3,4):
    value=struct.unpack_from('<I',payload,offset)[0]
    if value&0x1f800000==0x12000000 and (value>>29)&3 in [0,3] and decode_mask(value)==0xffffff00:
        candidates.append({'payload_offset':offset,'archived_container_offset':position+offset,
                           'static_address':hex(load+offset),'instruction':hex(value),
                           'rd':value&31,'rn':(value>>5)&31})
report={'scope':'Static binary candidates, not a proven function or runtime branch',
        'uboot_payload_sha256':hashlib.sha256(payload).hexdigest(),'payload_load':hex(load),
        'payload_bytes':size,'mask_candidates':candidates,'loader_execution_verified':False}
(out/'binary-candidates.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
