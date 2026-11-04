"""Extract factory camera wiring and resolve its graph and resource references."""
import hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
vendor=fdt((P/'vendor/ubuntu-5.10.160/boot-assets/board.dtb').read_bytes())
image=P/'outputs/armbian/official-f8-motion-s1/BOOT_ONLY_ARMBIAN_MOTION_S1.img'
blob=image.read_bytes();fit=fdt(blob);n=fit['/images/fdt'];a=int.from_bytes(n['data-position'],'big');length=int.from_bytes(n['data-size'],'big')
target=fdt(blob[a:a+length])
def decode(tree,path):
    values={}
    handles={int.from_bytes(v['phandle'],'big'):k for k,v in tree.items() if 'phandle' in v}
    for name,value in tree[path].items():
        if not value:values[name]=True
        elif name in ['compatible','status','clock-names','pinctrl-names','rockchip,camera-module-facing','rockchip,camera-module-name','rockchip,camera-module-lens-name','regulator-name']:values[name]=value.rstrip(b'\0').decode().split('\0')
        elif len(value)%4==0:
            cells=[int.from_bytes(value[i:i+4],'big') for i in range(0,len(value),4)]
            refs=cells if name.startswith('pinctrl-') and name!='pinctrl-names' else cells[:1] if name in ['clocks','power-domains','rockchip,grf','remote-endpoint','interrupt-parent','lens-focus','flash-leds'] or name.endswith('-supply') or name.endswith('gpios') else []
            values[name]={'cells':cells,'handle_paths':{str(n):handles[n] for n in refs if n in handles}} if refs else cells
        else:values[name]=value.hex()
    return values
selected={}
for label,tree in [('factory',vendor),('s1',target)]:
    paths={k for k in tree if any(s in k.lower() for s in ['gc5035','ov8858','rkisp','rkcif','csi2-dphy','csi2-dcphy','csi2@','dw9714']) or k=='/i2c@fead0000'}
    # Include resource providers referenced by sensor nodes, then one upstream supply level.
    for _ in range(2):
        for k in list(paths):
            if any(s in k for s in ['gc5035','ov8858']) or 'regulator' in k or 'vcc' in k:
                for name,value in tree[k].items():
                    if name in ['clocks','pinctrl-0','power-domains'] or name.endswith('gpios') or name.endswith('-supply'):
                        if len(value)>=4:
                            ph=value[:4];match=next((p for p,v in tree.items() if v.get('phandle')==ph),None)
                            if match:paths.add(match)
    selected[label]={k:decode(tree,k) for k in sorted(paths)}
out=P/'analysis/armbian/camera';out.mkdir(exist_ok=True)
(out/'dt-audit01.json').write_text(json.dumps(selected,indent=2)+'\n')
for label in selected:
    print(label)
    for path,props in selected[label].items():
        if any(s in path for s in ['gc5035','ov8858']) or path=='/i2c@fead0000':print(path,json.dumps(props))
