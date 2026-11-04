"""QPainter demonstrations driven exclusively by observed sensor samples."""
import math,subprocess
from PyQt6.QtCore import Qt,QPointF
from PyQt6.QtGui import QColor,QFont,QPainter,QPen,QPolygonF
from PyQt6.QtWidgets import QFrame,QGridLayout,QHBoxLayout,QLabel,QPushButton,QVBoxLayout,QWidget
from motion_examples_math import GyroPose,mapped,multiply,norm,rotate
from sensor_fusion import MotionFusion,conjugate,euler
from gyro_stabilizer import load_shared_bias,save_shared_bias

def note(text):
 w=QLabel(text);w.setWordWrap(True);w.setStyleSheet('color:#9eafc5;font-size:12px');return w
class Canvas(QWidget):
 def __init__(self,kind):super().__init__();self.kind=kind;self.data={};self.q=(1,0,0,0);self.perspective=False;self.setMinimumSize(260,210)
 def paintEvent(self,event):
  p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.fillRect(self.rect(),QColor('#111c2d'));p.setFont(QFont('Sans Serif',11));p.setPen(QColor('#d9e8f5'))
  cx,cy=self.width()/2,self.height()/2;r=min(self.width(),self.height())*.35
  if self.kind=='gyro':
   if not self.data.get('valid'):
    p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,self.data.get('invalid_note','等待陀螺仪真实读数'));return
   view=multiply((math.cos(.22),math.sin(.22),0,0),(math.cos(-.28),0,math.sin(-.28),0)) if self.perspective else (1,0,0,0);q=multiply(view,self.q)
   vertices=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
   points=[rotate(q,v) for v in vertices]
   def project(v):return QPointF(cx+v[0]*r*.65*4.8/(4.8-v[2]),cy-v[1]*r*.65*4.8/(4.8-v[2]))
   faces=[([0,1,2,3],'#344d74','Z−'),([4,5,6,7],'#267d98','Z+'),([0,4,7,3],'#685093','X−'),([1,5,6,2],'#967039','X+'),([0,1,5,4],'#304a68','Y−'),([3,2,6,7],'#348574','Y+')]
   for ids,color,text in sorted(faces,key=lambda f:sum(points[i][2] for i in f[0])):
    polygon=QPolygonF([project(points[i]) for i in ids]);p.setBrush(QColor(color));p.setPen(QPen(QColor('#b1cbe4'),1.2));p.drawPolygon(polygon)
    center=project([sum(points[i][axis] for i in ids)/4 for axis in range(3)]);p.setPen(QColor('#f0f7ff'));p.drawText(center+QPointF(-10,4),text)
   for axis,color,v in [('X','#67d8ef',(1.65,0,0)),('Y','#bc9aff',(0,1.65,0)),('Z','#ffbf6b',(0,0,1.65))]:
    end=project(rotate(q,v));p.setPen(QPen(QColor(color),2));p.drawLine(QPointF(cx,cy),end);p.drawText(end+QPointF(3,-3),axis)
  elif self.kind=='accel':
   p.setBrush(QColor('#17263b'));p.setPen(QPen(QColor('#40566e'),2));p.drawEllipse(QPointF(cx,cy),r,r);p.drawLine(QPointF(cx-r,cy),QPointF(cx+r,cy));p.drawLine(QPointF(cx,cy-r),QPointF(cx,cy+r))
   v=self.data.get('accel')
   if v:
    x=max(-1,min(1,v[0]/9.81));y=max(-1,min(1,v[1]/9.81));p.setBrush(QColor('#67d8ef'));p.setPen(Qt.PenStyle.NoPen);p.drawEllipse(QPointF(cx+x*r*.85,cy-y*r*.85),12,12)
    p.setPen(QColor('#d9e8f5'));pitch=math.degrees(math.atan2(-v[0],math.hypot(v[1],v[2])));roll=math.degrees(math.atan2(v[1],v[2]));p.drawText(8,self.height()-8,f'俯仰 {pitch:+.1f}°  横滚 {roll:+.1f}°  |a| {norm(v):.2f}')
   else:p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,'等待加速度读数')
  elif self.kind=='compass':
   cy-=10;r=min(self.width(),self.height())*.30
   p.setBrush(QColor('#17263b'));p.setPen(QPen(QColor('#40566e'),2));p.drawEllipse(QPointF(cx,cy),r,r)
   p.setPen(QColor('#d9e8f5'));heading=self.data.get('heading');angle=heading if heading is not None else 0
   for a,text in [(0,'北'),(90,'东'),(180,'南'),(270,'西')]:
    t=math.radians(a-angle);p.drawText(QPointF(cx+math.sin(t)*(r+12)-7,cy-math.cos(t)*(r+12)+5),text)
   if heading is None:
    p.drawText(self.rect().adjusted(0,0,0,-20),Qt.AlignmentFlag.AlignCenter,self.data.get('compass_note','等待磁场读数').replace('，','\n'))
    if 'field' in self.data:p.drawText(8,self.height()-8,f'原始磁场模长 {self.data["field"]:.1f} μT（含偏置）')
   else:
    p.save();p.translate(cx,cy);p.rotate(-heading);p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#67d8ef'));p.drawPolygon(QPolygonF([QPointF(0,-r*.8),QPointF(-10,12),QPointF(10,12)]));p.restore();p.setPen(QColor('#d9e8f5'));p.drawText(8,self.height()-8,f'磁航向 {heading:.0f}°  磁场 {self.data.get("field",0):.1f} μT')
  else:
   names={'normal':(0,'正向竖屏'),'bottom-up':(180,'倒置竖屏'),'left-up':(90,'左侧朝上'),'right-up':(-90,'右侧朝上'),'undefined':(0,'平放／方向未确定')};angle,title=names.get(self.data.get('orientation'),(0,'方向服务暂未就绪'))
   p.save();p.translate(cx,cy-18);p.rotate(angle);p.setBrush(QColor('#243c58'));p.setPen(QPen(QColor('#67d8ef'),2));p.drawRoundedRect(-40,-65,80,130,9,9);p.drawLine(0,-40,0,32);p.drawText(-8,-46,'↑');p.restore();p.setPen(QColor('#d9e8f5'));p.drawText(8,self.height()-45,title)
   cover=self.data.get('hall');motor=self.data.get('motor');temp=self.data.get('temperature')
   p.drawText(8,self.height()-25,'保护盖：'+('合上' if cover==0 else '打开' if cover==1 else '未提供')+' · 马达：'+('开启' if motor==1 else '关闭' if motor==0 else '未提供'))
   p.drawText(8,self.height()-5,('芯片温度：'+f'{temp:.1f} °C') if temp is not None else '芯片温度：未提供')

class Examples(QWidget):
 def __init__(self):
  super().__init__();self.pose=GyroPose();self.relative_fusion=MotionFusion();self.reference=None;self.relative_q=(1,0,0,0);self.was_calibrating=False;self.views={};self.state={};grid=QGridLayout(self);grid.setSpacing(12)
  items=[('gyro','陀螺仪 · 相对姿态正方体','六轴融合显示相对初始姿态，静止时抑制零偏漂移；Yaw非磁北。方块归零只重设显示参考。'),('accel','加速度 · 水平仪','静置时观察重力倾斜；移动时也包含线性加速度，不能当作精密姿态角。'),('compass','磁场 · 指南针','复用已保存的个人校准。平面校准仅平放；完成三轴校准后可倾斜读磁航向。'),('other','方向与其他状态','观察方向服务、真实保护盖开合和马达输出。温度为芯片温度。')]
  for index,(kind,title,description) in enumerate(items):
   frame=QFrame();frame.setObjectName('card');box=QVBoxLayout(frame);header=QLabel(title);header.setStyleSheet('font-size:17px;color:#e6eefb');box.addWidget(header)
   canvas=Canvas(kind);self.views[kind]=canvas;box.addWidget(canvas,1);box.addWidget(note(description))
   if kind=='gyro':
    buttons=QHBoxLayout();reset=QPushButton('方块归零');reset.clicked.connect(self.reset_relative);zero=QPushButton('静置校零');zero.clicked.connect(self.pose.calibrate);buttons.addWidget(reset);buttons.addWidget(zero);box.addLayout(buttons);self.message=note(self.pose.message);box.addWidget(self.message);self.relative_angles=note("相对角：等待数据");box.addWidget(self.relative_angles)
   if kind in ['compass','other']:
    button=QPushButton('打开指南针校准' if kind=='compass' else '打开霍尔与振动测试');button.clicked.connect(lambda checked=False,k=kind:subprocess.Popen(['/usr/local/bin/f8-compass' if k=='compass' else '/usr/local/bin/f8-cover-test'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL));box.addWidget(button)
   grid.addWidget(frame,index//2,index%2)
 def reset_relative(self):
  self.reference=self.relative_fusion.q;self.pose.reset()
 def update_sample(self,data):
  matrix=data.get('example_matrix',((1,0,0),(0,1,0),(0,0,1)));scaled=data.get('scaled',{});a=scaled.get('accel');w=scaled.get('anglvel');a=mapped(matrix,a) if a else None;w=mapped(matrix,w) if w else None
  if self.pose.samples is None:self.pose.bias=load_shared_bias() or self.pose.bias
  self.pose.advance(w,data.get('monotonic',0),a);self.message.setText(self.pose.message)
  if self.was_calibrating and self.pose.samples is None and self.pose.message.startswith('静置校零完成'):save_shared_bias(self.pose.bias)
  fused=self.relative_fusion.advance(a,w,data.get('monotonic',0),None,self.pose.bias)
  if fused.get('valid'):
   if self.reference is None or (self.was_calibrating and self.pose.samples is None):self.reference=fused['game_rotation_vector_wxyz']
   self.relative_q=multiply(conjugate(self.reference),fused['game_rotation_vector_wxyz'])
   angles=euler(self.relative_q);self.relative_angles.setText('相对 Yaw/Pitch/Roll  %+.1f° / %+.1f° / %+.1f°'%tuple(angles)+(' · 静止锁零' if fused.get('gyro_stationary') else ' · 运动中'))
  self.was_calibrating=self.pose.samples is not None
  common={'valid':w is not None,'accel':a,'orientation':data.get('orientation'),'temperature':data.get('temperature_c'),**data.get('aux',{}),**data.get('magnet',{})}
  for view in self.views.values():view.data=common;view.q=self.relative_q;view.update()
  self.state={'gyro_quaternion':self.relative_q,'pose_method':'six-axis gravity-stabilized relative to reference','gyro_stationary':fused.get('gyro_stationary',False),'gyro_bias_rad_s':self.pose.bias,'gyro_gap_count':self.pose.gaps,'matrix':matrix,'accel_board':a,'anglvel_board':w,'calibrating':self.pose.samples is not None,'message':self.pose.message,'magnet':data.get('magnet',{}),'aux':data.get('aux',{})}
