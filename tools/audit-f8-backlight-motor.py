import json,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
source=P/'outputs/armbian/official-f8-native-audio-a1/BOOT_ONLY_ARMBIAN_NATIVE_AUDIO_A1.img'
b=source.read_bytes();t=fdt(b);x=t['/images/fdt'];a=int.from_bytes(x['data-position'],'big');n=int.from_bytes(x['data-size'],'big')
report={}
for name,t in [('factory',fdt((P/'vendor/ubuntu-5.10.160/boot-assets/board.dtb').read_bytes())),('current',fdt(b[a:a+n]))]:
    refs={v['phandle']:k for k,v in t.items() if 'phandle' in v}
    pwm=refs[t['/backlight']['pwms'][:4]]
    pins=[]
    for i in range(0,len(t[pwm]['pinctrl-0']),4):
        path=refs[t[pwm]['pinctrl-0'][i:i+4]];raw=t[path]['rockchip,pins']
        pins.append({'path':path,'pins':[list(struct.unpack('>4I',raw[j:j+16]))[:3] for j in range(0,len(raw),16)]})
    report[name]={'pwm':pwm,'pwm_cells':list(struct.unpack('>'+str(len(t['/backlight']['pwms'])//4)+'I',t['/backlight']['pwms']))[1:],
                  'pinctrl':pins,'backlight_props':{k:v.hex() for k,v in t['/backlight'].items() if k not in ['brightness-levels','phandle']}}
dest=P/'analysis/armbian/backlight-motor-audit-20261030.json';dest.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
