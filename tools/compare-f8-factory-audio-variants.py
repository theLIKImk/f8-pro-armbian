import json,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
result={}
for path in [P/'vendor/ubuntu-5.10.160/boot-assets/board.dtb',*sorted((P/'analysis/update-ANDROID12').glob('dtb-*.dtb')),*sorted((P/'analysis/update-UBUNTU20.04').glob('dtb-*.dtb'))]:
    t=fdt(path.read_bytes());refs={v['phandle']:k for k,v in t.items() if 'phandle' in v}
    data={'model':t.get('/',{}).get('model',b'').decode(errors='replace').rstrip('\0'),'nodes':{}}
    for name,props in t.items():
        if not any(x in name.lower() for x in ['es8388','es8323','sound','vibrat','haptic']):continue
        selected={}
        for key,value in props.items():
            if key in ['compatible','status','rockchip,audio-routing','rockchip,card-name']:
                selected[key]=value.decode(errors='replace').rstrip('\0').split('\0')
            elif 'gpio' in key and len(value)>=12:
                selected[key]={'controller':refs.get(value[:4]),'cells':list(struct.unpack('>'+str((len(value)-4)//4)+'I',value[4:]))}
            elif key in ['out-l2spk-r2hp','use-ext-amplifier']:selected[key]=True
        if selected:data['nodes'][name]=selected
    result[str(path.relative_to(P))]=data
dest=P/'analysis/armbian/audio-factory-variants-20261030.json';dest.write_text(json.dumps(result,indent=2)+'\n')
for name,data in result.items():
    print(name,data['model'])
    for node,props in data['nodes'].items():
        gps={k:v for k,v in props.items() if 'gpio' in k}
        if gps:print(node,json.dumps(gps))
