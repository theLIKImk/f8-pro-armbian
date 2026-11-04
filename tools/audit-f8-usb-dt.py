"""Compare actual A3 USB DT with factory bindings; no device writes."""
import json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
image=P/'outputs/armbian/official-f8-native-audio-a3/BOOT_ONLY_ARMBIAN_NATIVE_AUDIO_A3.img'
b=image.read_bytes();fit=fdt(b);n=fit['/images/fdt'];pos=int.from_bytes(n['data-position'],'big');size=int.from_bytes(n['data-size'],'big')
trees={'a3':fdt(b[pos:pos+size]),'factory':fdt((P/'vendor/ubuntu-5.10.160/boot-assets/board.dtb').read_bytes())}
report={}
for label,tree in trees.items():
    selected={}
    for path,props in tree.items():
        if re.search(r'usb|typec|fusb|vbus',path,re.I) or b'fusb' in props.get('compatible',b''):
            selected[path]={k:(v.rstrip(b'\0').decode('ascii') if v and all(x==0 or 32<=x<127 for x in v) and not k in ['phandle','reg','gpios','clocks','phys','extcon','vbus-supply','rockchip,pins'] else v.hex()) for k,v in props.items()}
    report[label]=selected
out=P/'analysis/armbian/usb-a3-factory-dt-20261101.json';out.write_text(json.dumps(report,indent=2)+'\n')
for label,nodes in report.items():
    print(label)
    for path,props in nodes.items():
        if ('fusb' in str(props) or 'vbus' in path or 'usb@fc000000' in path or 'connector' in path):print(path,json.dumps(props))
