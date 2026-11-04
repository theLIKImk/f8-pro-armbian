import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'armbian/motion'))
from gyro_stabilizer import GyroStabilizer
s=GyroStabilizer()
for i in range(61):v=s.advance([.002,-.001,.0005],[0,0,9.81],i*.05)
assert s.stationary and v==[0,0,0]
v=s.advance([0,0,.3],[0,0,9.81],3.05)
assert not s.stationary and v[2]>.29
# Translating/shaking is never accepted as stationary gyro calibration.
s=GyroStabilizer()
for i in range(61):s.advance([.001,0,0],[.2*(-1)**i,0,9.81],i*.05)
assert not s.stationary and s.bias==[0,0,0]
# A genuine slow turn above the tiny noise band is retained.
s=GyroStabilizer()
for i in range(61):v=s.advance([0,0,.01],[0,0,9.81],i*.05)
assert not s.stationary and v==[0,0,.01]
# Explicit zero is subtracted once, and gap recovery requires another rest window.
s=GyroStabilizer()
for i in range(61):v=s.advance([.01,0,0],[0,0,9.81],i*.05,[.01,0,0])
assert s.stationary and v==[0,0,0]
s.advance([.01,0,0],[0,0,9.81],4,[.01,0,0]);assert not s.stationary
print('PASS: rest bias, movement rejection, slow turn retention, one-time manual bias and gap recovery')
