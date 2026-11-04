"""Verify archived guard/environment/DT-padding instruction anchors; offline."""
import hashlib
import json
from pathlib import Path
import struct

P=Path(__file__).resolve().parents[1]
out=P/'analysis/armbian/loader-placeholder'
data=(out/'uboot-ANALYSIS-ONLY.bin').read_bytes()
expected=json.loads((out/'binary-candidates.json').read_text())['uboot_payload_sha256']
assert hashlib.sha256(data).hexdigest()==expected
def word(offset):return struct.unpack_from('<I',data,offset)[0]
def call(offset):
    value=word(offset);assert value&0xfc000000==0x94000000
    imm=value&0x3ffffff
    if imm&(1<<25):imm-=1<<26
    return offset+imm*4
def string_pair(adrp,add):
    a=word(adrp);b=word(add)
    assert a&0x9f000000==0x90000000 and b&0xff000000==0x91000000
    assert a&31==(b>>5)&31
    immediate=((a>>5)&0x7ffff)<<2|((a>>29)&3)
    if immediate&(1<<20):immediate-=1<<21
    address=(adrp&~0xfff)+(immediate<<12)+(((b>>10)&0xfff)<<(12 if b&(1<<22) else 0))
    assert 0<=address<len(data)
    return data[address:data.index(b'\0',address)].decode()
assert string_pair(0x57b8,0x57c4)=='signature'
assert string_pair(0x57f4,0x5804)=='required'
assert string_pair(0x57fc,0x580c)=='conf'
anchors={0x57bc:0x52800001,0x5820:0xd2800003,0x5828:0xb50000c0,
         0x5840:0xaa1603e1,0x5848:0x35ffff20,0x584c:0x52800020,
         0x59d4:0xf9407240,0x5a4c:0x52800201,0x5a3c:0xd2800002,
         0x2afa8:0x91400ef6,0x2afc4:0xb100041f,
         0x2b0c4:0x5ac00ac0,0x2b0c8:0xb90006a0,0x2b0f4:0xf9000316}
for offset,value in anchors.items():assert word(offset)==value,hex(offset)
assert call(0x57d4)==0xa50d0 and call(0x5824)==0xa53f8 and call(0x5844)==0xbf474
mapping=[]
for name,prop,a,b,c,d,branch in [
        ('fdt_addr_r','fdt',0x5b10,0x5b18,0x5b14,0x5b1c,0x5b28),
        ('kernel_addr_r','kernel',0x5b30,0x5b38,0x5b34,0x5b3c,0x5b48),
        ('ramdisk_addr_r','ramdisk',0x5b5c,0x5b64,0x5b68,0x5b6c,None)]:
    assert string_pair(a,b)==name and string_pair(c,d)==prop
    if branch:assert call(branch)==0x5a28
    else:assert word(0x5b70)==0x17ffffae
    mapping.append({'fit_property':prop,'environment_key':name})
assert call(0x5a54)==0x15c3c
assert string_pair(0x2afa0,0x2afa4)=='fdt_high'
assert call(0x2afac)==0x15860
assert call(0x2b08c)==0xa4064
assert 'Using Device Tree in place at' in string_pair(0x2b0d4,0x2b0e4)
assert 'Loading Device Tree to' in string_pair(0x2b074,0x2b078)
report={'scope':'Original archived instruction/string dataflow anchors; no executed boot or active configuration observation',
        'payload_sha256':expected,
        'guard_signature_required_conf_structure_verified':True,
        'guard_called_with_gd_pointer_at_offset':224,
        'active_control_fdt_verified':False,'signature_policy_verified':False,
        'environment_mapping':mapping,'environment_parse_base':16,'environment_missing_default':0,
        'dt_relocation_function_offset':0x2af4c,'dt_expansion_bytes':0x3000,
        'fdt_high_all_ones_has_inplace_path':True,
        'inplace_path_increases_totalsize_without_copy':True,
        'inplace_backing_space_capacity_verified':False,
        'relocation_copy_call_offset':0x2b08c,
        'actual_fdt_high_verified':False,'runtime_load_addresses_verified':False,
        'final_memory_fixups_verified':False,'boot_ready':False}
live=json.loads((P/'analysis/armbian/live-loader-placement-2026-10-29.json').read_text())
assert live['kernel_release']=='5.10.160'
regions={row['label']:row['range'] for row in live['iomem_regions'] if row['label'].startswith('Kernel ')}
code_start=int(regions['Kernel code'].split('-')[0],16)
data_end=int(regions['Kernel data'].split('-')[1],16)+1
original=json.loads((P/'analysis/armbian/loader-contract.json').read_text())
report['old_running_kernel_observation']={
    'kernel_release':live['kernel_release'],'kernel_code_start':hex(code_start),
    'kernel_data_end_exclusive':hex(data_end),
    'visible_kernel_extent_bytes':data_end-code_start,
    'visible_extent_matches_archived_image_runtime_size':data_end-code_start==original['original_image_header']['runtime_image_bytes'],
    'initrd_start':live['chosen_initrd']['linux,initrd-start']['physical_address'],
    'initrd_end_exclusive':live['chosen_initrd']['linux,initrd-end']['physical_address'],
    'code_start_matches_embedded_default':code_start==int(original['embedded_default_address_variables']['kernel_addr_r'],16),
    'initrd_start_matches_embedded_default':int(live['chosen_initrd']['linux,initrd-start']['physical_address'],16)==int(original['embedded_default_address_variables']['ramdisk_addr_r'],16),
    'scope':'Old running kernel metadata; not new-kernel placement or proof of active environment contents'}
(out/'verified-handoff-paths.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
