from pathlib import Path
import math,sys,random
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'armbian/sensor-relay'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'armbian/motion'))
from browser_pose_math import *
from sensor_fusion import normalized,multiply,rotate,MotionFusion,conjugate

def axis(a,t):return (math.cos(t/2),*(math.sin(t/2) if i==a else 0 for i in range(3)))
def rebuild(d):return multiply(multiply(axis(2,math.radians(d['alpha'])),axis(0,math.radians(d['beta']))),axis(1,math.radians(d['gamma'])))
for _ in range(500):
 q=normalized([random.uniform(-1,1) for i in range(4)]);r=rebuild(device_euler(q));assert abs(sum(a*b for a,b in zip(q,r)))>1-1e-10
for a in range(3):
 for d in [0,30,60,89.9,90,90.1,120,179,180,240,270,359]:
  q=axis(a,math.radians(d));r=rebuild(device_euler(q));assert abs(sum(x*y for x,y in zip(q,r)))>1-1e-9,(a,d,device_euler(q))
# Reproduce Chromium156 Euler complementary filter after holding a true +X30 degree tilt.
b=g=0
for i in range(400):b=.98*b;g=.98*g+.02*(-math.sin(math.pi/6)*math.pi/2)
assert abs(b)<1e-8 and abs(math.degrees(g)+45)<.1
# F8 quaternion fusion keeps the same edge/axis after motion stops.
f=MotionFusion()
for i in range(201):
 t=i*.01;theta=min(t,1)*math.pi/6;q=axis(0,theta);a=rotate(conjugate(q),(0,0,9.80665));rate=(math.pi/6 if t<=1 else 0,0,0);s=f.advance(a,rate,t)
e=device_euler(s['game_rotation_vector_wxyz']);assert abs(e['beta']-30)<.3 and abs(e['gamma'])<.01
print('PASS: 500 quaternion/Euler roundtrips, all-axis edge angles, browser cross-axis regression and F8 held X-axis30 pose')
