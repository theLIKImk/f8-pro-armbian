"""Disassemble archived payload once and collect candidate string cross-references."""
import json
from pathlib import Path
import struct
import subprocess

P=Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
out=P/'analysis/armbian/loader-placeholder'
payload=out/'uboot-ANALYSIS-ONLY.bin'
data=payload.read_bytes()
assembly=out/'uboot-full-ANALYSIS-ONLY.asm'
with assembly.open('w') as stream:
    subprocess.run(['aarch64-linux-gnu-objdump','-D','-b','binary','-m','aarch64',str(payload)],stdout=stream,check=True)
names=[b'fdt_addr_r',b'kernel_addr_r',b'ramdisk_addr_r',b'signature',b'required',b'conf',
       b'fdt_high',b'Loading Device Tree to',b'Using Device Tree in place at',b'FDT_ERR_NOSPACE']
strings={}
for name in names:
    start=0
    while True:
        offset=data.find(name,start)
        if offset<0:break
        # Exact keys; diagnostic prefixes may continue after the searched text.
        if name in names[:7] and data[offset+len(name)]!=0:
            start=offset+1;continue
        strings[offset]=data[offset:data.find(b'\0',offset)].decode('utf-8',errors='replace')
        start=offset+1
refs=[]
for offset in range(0,len(data)-64,4):
    instruction=struct.unpack_from('<I',data,offset)[0]
    if instruction&0x9f000000!=0x90000000:continue
    register=instruction&31
    immediate=((instruction>>5)&0x7ffff)<<2 | ((instruction>>29)&3)
    if immediate&(1<<20):immediate-=1<<21
    page=(offset&~0xfff)+(immediate<<12)
    for following in range(offset+4,offset+32,4):
        add=struct.unpack_from('<I',data,following)[0]
        if add&0xff000000!=0x91000000 or (add>>5)&31!=register:continue
        target=page+(((add>>10)&0xfff)<<(12 if add&(1<<22) else 0))
        if target in strings:
            refs.append({'adrp_offset':offset,'add_offset':following,'string_offset':target,
                         'string':strings[target],'dataflow_verified':False})
lines=assembly.read_text().splitlines()
ranges=[('signature-guard',0x57b4,0x5898),('fit-preprocess',0x5ae8,0x5d80)]
for index,ref in enumerate(refs):
    if 'Device Tree' in ref['string'] or ref['string']=='fdt_high':
        ranges.append(('fdt-candidate-'+str(index),max(0,ref['adrp_offset']-300),ref['add_offset']+700))
for name,start,end in ranges:
    selected=[]
    for line in lines:
        field=line.strip().split(':',1)[0]
        try:address=int(field,16)
        except ValueError:continue
        if start<=address<end:selected.append(line)
    (out/(name+'.asm')).write_text('\n'.join(selected)+'\n')
report={'scope':'Candidate static string refs; ADRP/ADD matching alone is not dataflow proof',
        'refs':refs,'disassembly_bytes':assembly.stat().st_size,
        'runtime_environment_verified':False}
(out/'handoff-string-candidates.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
