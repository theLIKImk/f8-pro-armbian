import json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
b=(P/'outputs/armbian/official-f8-native-audio-a2/BOOT_ONLY_ARMBIAN_NATIVE_AUDIO_A2.img').read_bytes();t=fdt(b);p=t['/images/fdt'];a=int.from_bytes(p['data-position'],'big');n=int.from_bytes(p['data-size'],'big');tree=fdt(b[a:a+n])
report={path:{key:value.hex() for key,value in props.items()} for path,props in tree.items() if 'mclkout-i2s0' in path}
(P/'analysis/armbian/audio-mclk-nodes-20261030.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
