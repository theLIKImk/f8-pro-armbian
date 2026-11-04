"""Correlate G1 panic with regulator cleanup and exact official kernel callsites."""
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
E=P/'analysis/armbian/official-gpu-baseline-20261029'
out=E/'g1-failure';out.mkdir(exist_ok=True)
log=P/'local/hardware/armbian-official-g1-failure-20261029-01/pstore-01.txt'
text=log.read_text()
for marker in ['Linux version 6.1.115-vendor-rk35xx','systemd 259.5-0ubuntu3',
               'vdd_gpu_s0: disabling',"failed to set domain 'gpu'",'panic_on_set_domain',
               'panthor_init+']:
    assert marker in text,marker
root=Path(json.loads((E/'prepared-official-root.json').read_text())['root_directory'])
symbols={}
for line in (root/'boot/System.map-6.1.115-vendor-rk35xx').read_text().splitlines():
    parts=line.split()
    if len(parts)==3:symbols[parts[2]]=int(parts[0],16)
base=symbols['_text']
image=(root/'boot/vmlinuz-6.1.115-vendor-rk35xx').read_bytes()
ordered=sorted((address,name) for name,address in symbols.items() if name.startswith(('rockchip_pd_','regulator_')))
calls=[]
for function in ['rockchip_pd_power','rockchip_pd_power_on']:
    start=symbols[function]-base
    # Bound scan to the next mapped code symbol, not neighboring function data.
    end=min(address for name,address in symbols.items() if address>symbols[function])-base
    for offset in range(start,end,4):
        word=struct.unpack_from('<I',image,offset)[0]
        if word&0xfc000000!=0x94000000:continue
        imm=word&0x3ffffff
        if imm&0x2000000:imm-=0x4000000
        address=base+offset+imm*4
        names=[name for name,addr in symbols.items() if addr==address]
        calls.append({'function':function,'image_offset':hex(offset),'targets':names})
assert any('regulator_enable' in c['targets'] for c in calls),'Exact kernel regulator-enable call must be verified'
tree=fdt((P/'outputs/armbian/official-f8-graphics-r1b/boot-g1b/boot-graphics.NOT-APPROVED.dtb').read_bytes())
controller='/power-management@fd8d8000/power-controller'
rail='/spi@feb20000/rk806single@0/regulators/DCDC_REG1'
assert 'gpu-supply' not in tree[controller]
assert 'regulator-always-on' not in tree[rail]
source=Path('/var/tmp/f8-pro-armbian/linux-rockchip-config/drivers/soc/rockchip/pm_domains.c')
reference=None
if source.exists():
    data=source.read_bytes();(out/'pm_domains.reference-6.1.172.c').write_bytes(data)
    source_text=data.decode()
    reference={'path':str(source),'sha256':hashlib.sha256(data).hexdigest(),
               'version_scope':'6.1.172 source reference; exact 6.1.115 binary callsites checked separately'}
    excerpts=[]
    lines=source_text.splitlines()
    for i,line in enumerate(lines):
        if 'regulator_enable' in line or 'regulator_get_optional' in line:
            excerpts.append({'line':i+1,'text':'\n'.join(lines[max(0,i-8):i+10])})
    (out/'regulator-code-excerpts.json').write_text(json.dumps(excerpts,indent=2)+'\n')
report={'scope':'G1 failure evidence and targeted GPU power-domain supply fix rationale',
        'g1_panic_log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),
        'official_kernel_and_userspace_reached':True,'gpu_rail_disabled_seconds':33.848197,
        'gpu_domain_failure_seconds':41.763609,'panic_seconds':41.764651,
        'failure_path':'Panthor module registration -> genpd attach -> GPU power-domain on -> panic',
        'gpu_domain_supply_missing':True,'panthor_mali_supply_already_present':True,
        'exact_kernel_regulator_calls':calls,'source_reference':reference,
        'proposed_change':'Add gpu-supply on the power controller pointing to existing F8 DCDC_REG1',
        'voltage_constraints_will_change':False,'panic_guard_will_be_disabled':False,
        'hardware_fix_verified':False,
        'other_nonfatal_findings':['VOP missing supply/DVFS fallback','panel bpc=0 warning']}
(out/'failure-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
