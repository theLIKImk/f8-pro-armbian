"""Compare physical audio wiring in the frozen official-kernel DT and factory DT."""
import json,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
blob=(P/'outputs/armbian/official-f8-desktop-t1r2/BOOT_ONLY_ARMBIAN_NATIVE_DESKTOP_T1R2.img').read_bytes()
fit=fdt(blob);p=fit['/images/fdt'];a=int.from_bytes(p['data-position'],'big');n=int.from_bytes(p['data-size'],'big')
current=fdt(blob[a:a+n]);factory=fdt((P/'vendor/ubuntu-5.10.160/boot-assets/board.dtb').read_bytes())
def cells(b):return list(struct.unpack('>'+str(len(b)//4)+'I',b))
def refs(t):return {v['phandle']:k for k,v in t.items() if 'phandle' in v}
def ph(t,node,key):return refs(t)[t[node][key][:4]]
def pins(t,node):
    r=refs(t);result=[]
    for i in range(0,len(t[node]['pinctrl-0']),4):
        path=r[t[node]['pinctrl-0'][i:i+4]]
        data=t[path]['rockchip,pins']
        for j in range(0,len(data),16):
            v=cells(data[j:j+16]);cfg=t[r[data[j+12:j+16]]]
            result.append({'bank':v[0],'pin':v[1],'function':v[2],
                'config':{k:b.hex() for k,b in cfg.items() if k not in ['phandle','name']}})
    return result
sound='/es8388-sound';codec='/i2c@fec90000/es8388@11'
report={};differences=[]
for label,t in [('factory',factory),('current',current)]:
    cpu=ph(t,sound,'rockchip,cpu');assert ph(t,sound,'rockchip,codec')==codec
    report[label]={'cpu':cpu,'cpu_pins':pins(t,cpu),'cpu_clocks':cells(t[cpu]['clocks'])[1::2],
      'codec_mclk':cells(t[codec]['clocks'])[1:],'codec_rate':cells(t[codec]['assigned-clock-rates']),
      'codec_pins':pins(t,codec),'i2c_pins':pins(t,'/i2c@fec90000'),
      'voice_pins':pins(t,sound),'speaker_gpio_cells':cells(t[codec]['spk-con-gpio'])[1:]}
for key in report['factory']:
    if report['factory'][key]!=report['current'][key]:differences.append(key)
report['different_fields']=differences
report['battery_changes']=False
dest=P/'analysis/armbian/audio-wiring-20261030.json';dest.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
