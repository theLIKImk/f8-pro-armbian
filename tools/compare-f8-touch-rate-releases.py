import json
from pathlib import Path
root=Path('/var/lib/f8-pro/touch-rate');out=[]
for label in ['baseline1','p252-1','p157-1','p128-1','p122-2','p128-2']:
 d=json.loads((root/label/'result.json').read_text());f=d['frames']
 out.append({'round':label,'irq_hz':d['irq']['median_hz'],'evdev_frames':len(f),'release_transitions':sum(a['contacts']>b['contacts'] for a,b in zip(f,f[1:])),'zero_contact_frames':sum(x['contacts']==0 for x in f),'syn_dropped':d['syn_dropped']})
print(json.dumps(out,indent=2))
