"""Corroborate placeholder fixup structure in original U-Boot, not execution."""
import hashlib
import json
from pathlib import Path
import struct

P=Path(__file__).resolve().parents[1]
out=P/'analysis/armbian/loader-placeholder'
binary=(out/'uboot-ANALYSIS-ONLY.bin').read_bytes()
candidates=json.loads((out/'binary-candidates.json').read_text())
assert hashlib.sha256(binary).hexdigest()==candidates['uboot_payload_sha256']
pin=json.loads((P/'analysis/armbian/loader-source-reference/pin.json').read_text())
reference=(P/'analysis/armbian/loader-source-reference/arch/arm/mach-rockchip/fit.c').read_text()
assert '(addr & 0xffffff00) == FIT_PLACEHOLDER_ADDR' in reference
assert 'fit_sig_require_conf(fit, gd_fdt_blob())' in reference
def word(offset):return struct.unpack_from('<I',binary,offset)[0]
def branch(offset,link=True):
    value=word(offset)
    assert value&0xfc000000==(0x94000000 if link else 0x14000000)
    imm=value&0x3ffffff
    if imm&(1<<25):imm-=1<<26
    return offset+imm*4
anchors={0x5998:0xa9bd7bfd,0x599c:0x92785c42,0x59ac:0xb2785fe0,
         0x59b4:0xeb00005f,0x59b8:0x540000e0,0x59bc:0x52800013,
         0x59e4:0x35fffec0,0x5ac4:0x1107fc42,0x5ac8:0x12175842,
         0x5ad8:0x12800160}
for offset,value in anchors.items():assert word(offset)==value,hex(offset)
assert branch(0x59e0)==0x57b4
assert branch(0x59f0)==0x5854
assert branch(0x5a08)==0x2bb1c
assert branch(0x5a24,False)==0x2bafc
assert branch(0x5ab0)==0x5998
report={'scope':'Static archived instruction anchors with source correspondence; not boot/runtime-address verification',
        'payload_sha256':candidates['uboot_payload_sha256'],
        'reference_commit':pin['commit'],'reference_exact_firmware_source':False,
        'fixup_function_payload_offset':0x5998,'mask_and_compare_verified':True,
        'non_placeholder_returns_without_fixup':True,
        'guard_call_payload_offset':0x57b4,'guard_callee_identity_verified':False,
        'post_guard_default_node_call':0x5854,
        'two_write_callees_inferred_as_entry_and_load':[0x2bb1c,0x2bafc],
        'allocation_caller_uses_payload_size_rounded_to_512':True,
        'new_reference_fdt_padding_branch_seen_in_archived_allocation_function':False,
        'later_fdt_expansion_verified':False,'runtime_environment_verified':False,
        'signature_policy_verified':False,'boot_ready':False}
(out/'verified-fixup-structure.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
