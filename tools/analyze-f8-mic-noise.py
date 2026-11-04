"""Local statistics only: no audio leaves the tablet."""
import array,json,math,os,wave
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
p=Path('/home/likimk/.cache/f8-mic-check-20261102/results.json');d=json.loads(p.read_text());out={}
for mode,result in d['trials'].items():
 src=Path(result['file']);assert src.parent==p.parent
 with wave.open(str(src),'rb') as w:
  rate=w.getframerate();a=array.array('h',w.readframes(w.getnframes()))
 rows=[]
 for ch in [0,1]:
  data=a[ch::2];parts={}
  for label,start,end in [('quiet',10.5,13.5),('speech',6.5,9.5)]:
   x=data[int(start*rate):int(end*rate)];mean=sum(x)/len(x);std=math.sqrt(sum((v-mean)**2 for v in x)/len(x))
   parts[label]={'mean':mean,'std':std,'peak':max(abs(v) for v in x)}
   try:
    import numpy as np
    y=np.asarray(x,dtype=float);y-=y.mean();power=abs(np.fft.rfft(y*np.hanning(len(y))))**2;freq=np.fft.rfftfreq(len(y),1/rate)
    parts[label]['power_fraction']={str(low)+'-'+str(high):float(power[(freq>=low)&(freq<high)].sum()/max(power.sum(),1e-20)) for low,high in [(0,30),(30,80),(80,300),(300,4000),(4000,24000)]}
   except ImportError:pass
  rows.append(parts)
 out[mode]=rows
print(json.dumps(out,indent=2))
