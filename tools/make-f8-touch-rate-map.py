"""Integer target table from measured period/interval knots; untested entries are estimates."""
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
knots=[(122,8.325),(128,8.733),(157,10.492),(252,13.308),(280,14.768)]
rates={}
for hz in range(60,121):
 t=1000/hz;pair=(knots[-2],knots[-1])
 for a,b in zip(knots,knots[1:]):
  if a[1]<=t<=b[1]:pair=(a,b);break
 a,b=pair;period=round(a[0]+(t-a[1])*(b[0]-a[0])/(b[1]-a[1]))
 assert 122<=period<=320
 rates[str(hz)]={'period':period,'estimated':True}
assert all(rates[str(h)]['period']>rates[str(h+1)]['period'] for h in range(60,120))
assert rates['120']['period']==122 and abs(rates['75']['period']-252)<=1
result={'target_range':[60,120],'unit':'Hz','mapping_method':'piecewise linear interpolation in period versus measured interval; extrapolate below measured 67.7Hz','measured_knots':[{'period':p,'interval_ms':t,'hz':1000/t} for p,t in knots],'rates':rates,'note':'Targets are integer requests, not guaranteed exact or stable hardware frequencies. Actual IRQ rate is displayed during touch.'}
dest=P/'armbian/touch/rate-map.json';dest.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({h:rates[str(h)] for h in [60,68,75,90,100,115,120]}))
