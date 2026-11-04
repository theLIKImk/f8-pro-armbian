import math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'armbian/motion'))
from motion_examples_math import GyroPose,mapped,norm,rotate
p=GyroPose()
for i in range(21):p.advance([0,0,math.pi/2],i*.05,[0,0,9.81])
v=rotate(p.q,(1,0,0));assert max(abs(a-b) for a,b in zip(v,(0,1,0)))<1e-9
old=p.q;p.advance([0,0,1],3,[0,0,9.81]);assert p.q==old and p.gaps==1
p=GyroPose();p.calibrate()
for i in range(41):p.advance([.01,-.02,.005],i*.05,[0,0,9.81])
assert max(abs(a-b) for a,b in zip(p.bias,[.01,-.02,.005]))<1e-12
assert max(abs(a-b) for a,b in zip(p.q,[1,0,0,0]))<1e-12
p=GyroPose();p.calibrate()
for i in range(32):p.advance([.2*(-1)**i,0,0],i*.05,[0,0,9.81])
assert p.bias==[0,0,0] and '移动' in p.message
p=GyroPose()
for i in range(1001):p.advance([.1,.2,.3],i*.01)
assert abs(norm(p.q)-1)<1e-12
assert mapped([[0,-1,0],[-1,0,0],[0,0,-1]],[1,2,3])==[-2,-1,-3]
print('PASS: 90-degree rotation, gap rejection, session bias, moving rejection, unit quaternion, board mapping')
