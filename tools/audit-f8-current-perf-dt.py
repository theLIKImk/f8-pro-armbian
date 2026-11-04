from pathlib import Path
import json,sys,struct
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
b=(P/'outputs/armbian/official-f8-camera-c4/BOOT_ONLY_ARMBIAN_CAMERA_C4.img').read_bytes();t=fdt(b)
q=t['/images/fdt'];a=int.from_bytes(q['data-position'],'big');n=int.from_bytes(q['data-size'],'big');d=fdt(b[a:a+n])
def show(v):
 if v.endswith(b'\0') and all(c==0 or 32<=c<127 for c in v):return v.rstrip(b'\0').decode()
 if len(v)%4==0:return ['0x'+format(x,'x') for x in struct.unpack('>'+str(len(v)//4)+'I',v)]
 return v.hex()
out={p:{k:show(v) for k,v in props.items()} for p,props in d.items() if ('gpu' in p or p.startswith('/cpus/') or 'cluster' in p) and '/pinctrl/' not in p}
handles={int.from_bytes(v['phandle'],'big'):p for p,v in d.items() if 'phandle' in v}
references={}
for p,v in d.items():
 if p.startswith('/cpus/cpu@') or p=='/gpu-panthor@fb000000':
  for key in ['cpu-supply','mali-supply','sram-supply','mem-supply','operating-points-v2']:
   if key not in v:continue
   target=handles.get(int.from_bytes(v[key],'big'));references[p+'/'+key]={'target':target,'properties':{k:show(x) for k,x in d.get(target,{}).items()}}
out['resolved_references']=references
dest=P/'analysis/linux-issues-20261102';dest.mkdir(exist_ok=True)
(dest/'current-perf-dt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({p:v for p,v in out.items() if 'gpu' in p or p=='resolved_references'},indent=2))
