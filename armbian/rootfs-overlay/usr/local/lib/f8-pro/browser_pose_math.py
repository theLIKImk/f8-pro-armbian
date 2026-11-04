"""W3C Z-X-Y device orientation conversion, independent of browser fusion."""
import math

def quaternion_xyzw(q):
 if q is None or len(q)!=4 or not all(math.isfinite(v) for v in q):return None
 n=math.sqrt(sum(v*v for v in q))
 if not .9<n<1.1:return None
 return [q[1]/n,q[2]/n,q[3]/n,q[0]/n]

def device_euler(q):
 v=quaternion_xyzw(q)
 if v is None:return None
 x,y,z,w=v
 r00=1-2*(y*y+z*z);r01=2*(x*y-z*w)
 r10=2*(x*y+z*w);r11=1-2*(x*x+z*z)
 r20=2*(x*z-y*w);r21=2*(y*z+x*w);r22=1-2*(x*x+y*y)
 b=math.asin(max(-1,min(1,r21)))
 if abs(math.cos(b))<1e-7:a=math.atan2(r10,r00);g=0.
 else:
  a=math.atan2(-r01,r11);g=math.atan2(-r20,r22)
  if abs(g)>math.pi/2:
   a+=math.pi;b=math.pi-b if b>=0 else -math.pi-b
   g=g-math.pi if g>0 else g+math.pi
 return {'alpha':math.degrees(a)%360,'beta':math.degrees(b),'gamma':math.degrees(g)}
