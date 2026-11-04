"""Stationary-only zero-rate correction; no angle snapping or magnetic offset edits."""
import math,collections
class GyroStabilizer:
 def __init__(self):self.samples=collections.deque();self.bias=[0.,0.,0.];self.manual=None;self.last=None;self.stationary=False
 def advance(self,rate,accel,stamp,manual=(0,0,0)):
  if self.manual!=tuple(manual):self.bias=[0.,0.,0.];self.samples.clear();self.manual=tuple(manual)
  if self.last is not None and not 0<stamp-self.last<=.25:self.samples.clear()
  self.last=stamp;raw=[rate[i]-manual[i] for i in range(3)];corrected=[raw[i]-self.bias[i] for i in range(3)];self.stationary=False
  # This small threshold distinguishes rest noise from ordinary deliberate turns.
  if not 9<math.sqrt(sum(v*v for v in accel))<10.7 or math.sqrt(sum(v*v for v in corrected))>.004:
   self.samples.clear();return corrected
  self.samples.append((stamp,raw,list(accel)))
  while self.samples and stamp-self.samples[0][0]>2:self.samples.popleft()
  if len(self.samples)<20 or stamp-self.samples[0][0]<1.5:return corrected
  n=len(self.samples);m=[[sum(s[k][i] for s in self.samples)/n for i in range(3)] for k in [1,2]]
  spread=[math.sqrt(sum(sum((s[k][i]-m[k-1][i])**2 for i in range(3)) for s in self.samples)/n) for k in [1,2]]
  if spread[0]>.0015 or spread[1]>.055:return corrected
  self.stationary=True
  for i in range(3):self.bias[i]=.8*self.bias[i]+.2*m[0][i]
  return [0.,0.,0.]


def load_shared_bias():
 import os,json
 from pathlib import Path
 try:
  p=Path(os.environ['XDG_RUNTIME_DIR'])/'f8-gyro-bias.json';d=json.loads(p.read_text())
  boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
  b=d['bias_rad_s'];assert d['version']==1 and d['boot_id']==boot and d['frame']=='board' and len(b)==3 and all(math.isfinite(v) and abs(v)<.1 for v in b)
  return list(b)
 except (OSError,ValueError,KeyError,TypeError,AssertionError):return None

def save_shared_bias(bias):
 import os,json,time
 from pathlib import Path
 try:
  p=Path(os.environ['XDG_RUNTIME_DIR'])/'f8-gyro-bias.json';tmp=p.with_suffix('.tmp')
  boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
  data={'version':1,'frame':'board','bias_rad_s':list(bias),'boot_id':boot,'monotonic':time.monotonic(),'source':'explicit stationary calibration; current boot only'}
  fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
  with os.fdopen(fd,'w') as f:json.dump(data,f)
  os.replace(tmp,p)
 except (OSError,KeyError):pass
