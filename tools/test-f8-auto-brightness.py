from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'armbian/sensor-relay'))
from brightness_policy import *
assert 12<=target_percent(3)<=16
assert target_percent(12)==35
assert target_percent(4095)<=90
assert target_percent(500)>target_percent(12)>target_percent(3)
p=BrightnessPolicy();cur=28
for n in range(160):
 r=p.update(12,cur,n*.15)
 if r is not None:assert abs(r-cur)<=.40000001;cur=r
assert abs(cur-35)<=2
assert p.update(12,10,30) is None and p.pause_until==90
assert p.update(12,10,40) is None
assert p.update(4095,30,140,blocked=True) is None
assert p.update(4095,30,141,enabled=False) is None
print('Brightness mapping, slew limit, manual override and blocked states passed')
