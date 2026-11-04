import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'armbian/motion'))
from sensor_fusion import *
g=9.80665
for a in [(0,0,g),(0,g,0),(g,0,0),(0,0,-g)]:
 f=MotionFusion()
 for i in range(100):s=f.advance(a,(0,0,0),i*.05)
 assert norm(s['linear_acceleration_m_s2'])<1e-9
 assert abs(norm(s['gravity_m_s2'])-g)<1e-9
f=MotionFusion()
for i in range(21):s=f.advance((0,0,g),(0,0,math.pi/2),i*.05)
v=rotate(s['game_rotation_vector_wxyz'],(1,0,0));assert max(abs(x-y) for x,y in zip(v,(0,1,0)))<1e-9
f=MotionFusion();f.advance((0,0,g),(0,0,0),0);s=f.advance((1,0,g),(0,0,0),.001);assert s['linear_acceleration_m_s2'][0]>.9
s=f.advance((0,0,4*g),(0,0,0),.002);assert not s['gravity_correction_active']
for raw,expected in [((-50,0,0),180),((0,50,0),270),((50,0,0),0),((0,-50,0),90)]:assert abs(wrap(flat_heading(raw)-expected))<1e-8
# Independently rotate true gravity/north into the body frame, including roll/pitch.
qt=normalized(multiply(yaw_quat(.8),multiply((math.cos(.3),math.sin(.3),0,0),(math.cos(-.2),0,math.sin(-.2),0))))
a=rotate(conjugate(qt),(0,0,g));mb=rotate(conjugate(qt),(0,45,-10));raw=board_magnet(mb)
mp=magnetic_pose(a,raw);expected=normalized(multiply(yaw_quat(-math.pi),qt));assert abs(abs(dot(mp['quaternion'],expected))-1)<1e-9
f=MotionFusion();s=f.advance(a,(0,0,0),1,{'full_3d':True,'corrected_ut':raw,'monotonic':1});assert s['absolute_valid'];assert abs(abs(dot(s['rotation_vector_wxyz'],expected))-1)<1e-8
s=f.advance(a,(0,0,0),1.1,{'full_3d':False,'corrected_ut':raw,'monotonic':1.1});assert not s['absolute_valid'] and s['rotation_vector_wxyz'] is None
assert not f.advance((math.nan,0,g),(0,0,0),2)['valid']
f=MotionFusion();f.advance((0,0,g),(0,0,0),0);s=f.advance((0,0,g),(0,0,0),1);assert s['gap_count']==1
assert magnetic_pose((0,0,g),(0,0,0)) is None
print('PASS: static poses, gravity subtraction, yaw rotation, dynamic trust, four headings +180, tilted geomagnetic/9-axis pose, stale/invalid data, gaps, weak field')

f=MotionFusion();m={'full_3d':True,'corrected_ut':raw,'monotonic':1.04}
s=f.advance(a,(0,0,0),1,m);assert s['absolute_valid'] and not s['mag_prediction_only']
s=f.advance(a,(0,0,0),1.1,{'full_3d':True,'measurement_valid':False});assert s['absolute_valid'] and s['mag_prediction_only']
for t in [1.3,1.5,1.7,1.9,2.1,2.3]:s=f.advance(a,(0,0,0),t,{'full_3d':True,'measurement_valid':False})
assert not s['absolute_valid'] and s['rotation_vector_wxyz'] is None
print('PASS: sequential acquisition timestamp skew, bounded gyro prediction, expiration')
