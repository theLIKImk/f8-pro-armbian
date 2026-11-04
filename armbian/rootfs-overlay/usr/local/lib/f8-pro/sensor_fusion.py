"""Board-frame 6-axis complementary fusion and calibrated magnetic tilt compensation.
Quaternion rotates board coordinates to east/north/up; heading is clockwise from north.
Outputs are engineering estimates, not Android HAL or calibrated navigation results.
"""
import math
from motion_examples_math import norm,multiply,rotate
from gyro_stabilizer import GyroStabilizer
HEADING_OFFSET_DEG=180.0  # User requested north/south reversal; shared by both viewers.
MAG_MATRIX=((0,-1,0),(-1,0,0),(0,0,-1))

def finite(v):return v is not None and len(v)==3 and all(math.isfinite(x) for x in v)
def unit(v):
 n=norm(v)
 return tuple(x/n for x in v) if n>1e-9 else None
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def conjugate(q):return (q[0],-q[1],-q[2],-q[3])
def normalized(q):
 n=norm(q);return tuple(x/n for x in q) if n>1e-12 else (1.,0.,0.,0.)
def wrap(deg):return (deg+180)%360-180
def yaw_quat(angle):return (math.cos(angle/2),0.,0.,math.sin(angle/2))
def euler(q):
 w,x,y,z=q
 return [math.degrees(math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))),math.degrees(math.asin(max(-1,min(1,2*(w*y-z*x))))),math.degrees(math.atan2(2*(w*x+y*z),1-2*(x*x+y*y)))]
def from_up(a):
 u=unit(a)
 if u is None:return (1.,0.,0.,0.)
 if u[2]<-.999999:return (0.,1.,0.,0.)
 axis=cross(u,(0,0,1));return normalized((1+u[2],*axis))
def matrix_quaternion(m):
 tr=sum(m[i][i] for i in range(3))
 if tr>0:
  s=math.sqrt(tr+1)*2;q=(.25*s,(m[2][1]-m[1][2])/s,(m[0][2]-m[2][0])/s,(m[1][0]-m[0][1])/s)
 else:
  i=max(range(3),key=lambda k:m[k][k]);j=(i+1)%3;k=(j+1)%3;s=math.sqrt(max(0,1+m[i][i]-m[j][j]-m[k][k]))*2
  if s<1e-10:return (1.,0.,0.,0.)
  v=[0.,0.,0.];v[i]=.25*s;v[j]=(m[j][i]+m[i][j])/s;v[k]=(m[k][i]+m[i][k])/s;q=((m[k][j]-m[j][k])/s,*v)
 return normalized(q)
def board_magnet(corrected):return tuple(sum(a*b for a,b in zip(row,corrected)) for row in MAG_MATRIX)
def flat_heading(corrected):
 if not finite(corrected):return None
 bx,by,_=board_magnet(corrected)
 return (math.degrees(math.atan2(-bx,by))+HEADING_OFFSET_DEG)%360 if math.hypot(bx,by)>1 else None

def magnetic_pose(accel_board,corrected_magnet):
 if not finite(accel_board) or not finite(corrected_magnet):return None
 up=unit(accel_board);m=board_magnet(corrected_magnet)
 if up is None or not 10<=norm(m)<=120:return None
 horizontal=tuple(m[i]-up[i]*dot(m,up) for i in range(3));north=unit(horizontal)
 if north is None or norm(horizontal)<3:return None
 east=unit(cross(north,up))
 if east is None:return None
 q=matrix_quaternion((east,north,up));q=normalized(multiply(yaw_quat(math.radians(-HEADING_OFFSET_DEG)),q))
 forward=rotate(q,(0,1,0));h=math.hypot(forward[0],forward[1])
 return {'quaternion':q,'heading':math.degrees(math.atan2(forward[0],forward[1]))%360 if h>.15 else None,'field_ut':norm(m)}

class MotionFusion:
 def __init__(self):self.reset()
 def reset(self):
  self.q=(1.,0.,0.,0.);self.q9=self.q;self.last=None;self.initialized=False;self.mag_initialized=False;self.last_mag_stamp=None;self.mag_good_stamp=None;self.gaps=0;self.bias=(0.,0.,0.);self.stabilizer=GyroStabilizer()
 def advance(self,accel,rate,stamp,magnet=None,bias=(0,0,0)):
  if not finite(accel) or not finite(rate) or not math.isfinite(stamp):
   self.last=None;self.initialized=False;self.mag_good_stamp=None
   return {'valid':False,'status':'等待有效加速度及角速度'}
  if not finite(bias):bias=(0,0,0)
  dt=0 if self.last is None else stamp-self.last;self.last=stamp
  if dt<0 or dt>.25:self.gaps+=1;self.initialized=False;self.mag_initialized=False;self.mag_good_stamp=None;dt=0
  if not self.initialized:
   if not 7<norm(accel)<12:return {'valid':False,'status':'重力初始化需静置'}
   self.q=from_up(accel);self.q9=self.q;self.initialized=True
  # Changing session zero removes an estimated bias, not a new physical rotation.
  self.bias=tuple(bias);corrected_rate=self.stabilizer.advance(rate,accel,stamp,bias);g=9.80665;an=norm(accel);au=unit(accel)
  trust=max(0.,1-abs(an-g)/(g*.18));correcting=trust>.2
  def integrate(q):
   estimated=rotate(conjugate(q),(0,0,1));err=cross(au,estimated) if au else (0,0,0)
   omega=[corrected_rate[i]+2.0*trust*err[i] for i in range(3)];speed=norm(omega)
   if dt>0 and speed>1e-10:
    half=speed*dt/2;dq=(math.cos(half),*(v/speed*math.sin(half) for v in omega));q=normalized(multiply(q,dq))
   return q
  self.q=integrate(self.q);self.q9=integrate(self.q9)
  gravity=rotate(conjugate(self.q),(0,0,g));linear=tuple(accel[i]-gravity[i] for i in range(3))
  mag=magnet or {};mp=None;mag_status='需三轴磁场校准；当前仅六轴融合'
  calibrated=bool(mag.get('full_3d'))
  if not calibrated:self.mag_initialized=False;self.mag_good_stamp=None
  mag_stamp=mag.get('monotonic')
  if mag.get('full_3d') and finite(mag.get('corrected_ut')) and isinstance(mag_stamp,(int,float)) and -.25<=stamp-mag_stamp<1.2:
   mp=magnetic_pose(gravity,mag['corrected_ut'])
   if mp:
    mag_status='三轴校准磁场可用（仍受环境干扰）'
    if mag_stamp!=self.last_mag_stamp:
     target=euler(mp['quaternion'])[0];current=euler(self.q9)[0];diff=wrap(target-current)
     elapsed=.4 if self.last_mag_stamp is None else max(0,min(1,mag_stamp-self.last_mag_stamp))
     gain=1. if not self.mag_initialized else 1-math.exp(-elapsed/1.5)
     self.q9=normalized(multiply(yaw_quat(math.radians(diff*gain)),self.q9));self.mag_initialized=True
     self.last_mag_stamp=mag_stamp;self.mag_good_stamp=stamp
   else:mag_status='磁场过强/过弱或水平分量不足，暂停磁场约束'
  elif mag.get('full_3d'):mag_status='磁场采样失效或过期，暂停磁场约束'
  # Sequential sysfs reads can timestamp magnet data slightly after the IMU.
  # Bridge a short actual magnetic dropout with gyro prediction, explicitly marked.
  reference_age=max(0,stamp-self.mag_good_stamp) if self.mag_good_stamp is not None else None
  absolute=calibrated and self.mag_initialized and reference_age is not None and reference_age<1.2
  predicting=absolute and mp is None
  if predicting:mag_status='磁场短暂中断，使用陀螺仪预测（最多1.2秒）'
  q9=self.q9 if absolute else None
  heading=None
  if q9:
   forward=rotate(q9,(0,1,0))
   if math.hypot(forward[0],forward[1])>.15:heading=math.degrees(math.atan2(forward[0],forward[1]))%360
  return {'valid':True,'corrected_angular_velocity_rad_s':corrected_rate,'gyro_stationary':self.stabilizer.stationary,'gyro_auto_bias_rad_s':list(self.stabilizer.bias),'gyro_manual_bias_rad_s':list(bias),'game_rotation_vector_wxyz':self.q,'rotation_vector_wxyz':q9,'geomagnetic_rotation_vector_wxyz':mp['quaternion'] if mp else None,'gravity_m_s2':gravity,'linear_acceleration_m_s2':linear,'euler6_yaw_pitch_roll_deg':euler(self.q),'euler9_yaw_pitch_roll_deg':euler(q9) if q9 else None,'heading_deg':heading,'tilt_heading_deg':mp['heading'] if mp else None,'gravity_correction_active':correcting,'accel_trust':trust,'absolute_valid':absolute,'mag_calibrated_3d':calibrated,'mag_prediction_only':predicting,'magnetic_reference_age_s':reference_age,'magnetic_status':mag_status,'gap_count':self.gaps,'status':'六轴融合；快速运动/持续加速会影响估计','heading_offset_deg':HEADING_OFFSET_DEG}
