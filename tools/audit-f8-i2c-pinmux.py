"""Compare physical default I2C pinmux against factory evidence, not phandle IDs."""
import json
from pathlib import Path
import struct
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
factory=fdt((P/'vendor/ubuntu-5.10.160/boot-assets/board.dtb').read_bytes())
candidate=fdt((P/'outputs/armbian/official-f8-touch-g3/touch-g3.dtb').read_bytes())
def pins(tree,path):
    refs={v['phandle']:k for k,v in tree.items() if 'phandle' in v}
    result=[];groups=[]
    data=tree[path].get('pinctrl-0',b'')
    for index in range(0,len(data),4):
        group=refs[data[index:index+4]];groups.append(group)
        raw=tree[group].get('rockchip,pins',b'');assert len(raw)%16==0
        for start in range(0,len(raw),16):
            bank,pin,function,config=struct.unpack_from('>IIII',raw,start)
            config_path=refs[struct.pack('>I',config)]
            properties={k:v.hex() for k,v in tree[config_path].items() if k!='phandle'}
            result.append({'bank':bank,'pin':pin,'function':function,'config':properties})
    return groups,sorted(result,key=lambda x:(x['bank'],x['pin']))
rows=[]
for path,props in factory.items():
    if path.count('/')!=1 or not path.startswith('/i2c@') or path not in candidate:continue
    if props.get('status',b'okay\0')==b'disabled\0':continue
    a,ap=pins(factory,path);b,bp=pins(candidate,path)
    rows.append({'node':path,'factory_groups':a,'candidate_groups':b,'factory_pins':ap,'candidate_pins':bp,
                 'physical_mux_equal':ap==bp,'candidate_status':candidate[path].get('status',b'okay\0').decode().rstrip('\0')})
out=P/'analysis/armbian/official-gpu-baseline-20261029/touch-abi/i2c-pinmux-audit.json'
out.write_text(json.dumps({'scope':'Static physical pinmux comparison for future peripheral activation',
                           'rows':rows,'differences':[r['node'] for r in rows if not r['physical_mux_equal']]},indent=2)+'\n')
print(json.dumps({'differences':[r for r in rows if not r['physical_mux_equal']]},indent=2))
