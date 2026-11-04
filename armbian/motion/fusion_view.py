"""Interactive motion fusion/optical page, with user-private timestamped JSON output."""
import json,math,os,time
from pathlib import Path
from PyQt6.QtCore import Qt,QPointF
from PyQt6.QtGui import QColor,QPainter,QPen
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QGridLayout,QLabel,QComboBox,QHBoxLayout,QPushButton,QFrame,QProgressBar,QMessageBox
from sensor_examples import Canvas,note
from motion_examples_math import mapped,norm
from sensor_fusion import MotionFusion
class VectorView(QWidget):
 def __init__(self):super().__init__();self.data={};self.setMinimumSize(260,210)
 def paintEvent(self,event):
  p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.fillRect(self.rect(),QColor('#111c2d'));p.setPen(QColor('#d9e8f5'))
  if not self.data.get('valid'):p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,'等待真实读数');return
  cx,cy=self.width()/2,self.height()/2-25;r=min(self.width()*.4,self.height()*.3)
  p.setPen(QPen(QColor('#40566e'),1));p.drawEllipse(QPointF(cx,cy),r,r);p.drawLine(QPointF(cx-r,cy),QPointF(cx+r,cy));p.drawLine(QPointF(cx,cy-r),QPointF(cx,cy+r))
  for key,scale,color in [('gravity_m_s2',9.80665,'#67d8ef'),('linear_acceleration_m_s2',3,'#ffbf6b')]:
   v=self.data[key];end=QPointF(cx+max(-1,min(1,v[0]/scale))*r,cy-max(-1,min(1,v[1]/scale))*r)
   p.setPen(QPen(QColor(color),4));p.drawLine(QPointF(cx,cy),end);p.drawEllipse(end,4,4)
  p.setPen(QColor('#67d8ef'));g=self.data['gravity_m_s2'];p.drawText(8,self.height()-40,'重力 XYZ  %+.2f  %+.2f  %+.2f'%tuple(g))
  p.setPen(QColor('#ffbf6b'));v=self.data['linear_acceleration_m_s2'];p.drawText(8,self.height()-18,'运动 XYZ  %+.2f  %+.2f  %+.2f'%tuple(v))
class FusionPanel(QWidget):
 def __init__(self,gyro_pose):
  super().__init__();self.pose=gyro_pose;self.fusion=MotionFusion();self.state={};self.last_publish=0
  self.path=Path('/run/user')/str(os.getuid())/'f8-sensor-fusion.json'
  self.optical_path=Path.home()/'.config/f8-pro/optical-calibration.json';self.optical_cal=None;self.pending_far=None;self.near=None;self.initial_mode_set=False
  try:
   c=json.loads(self.optical_path.read_text());assert c['version']==1 and 0<=c['far']<c['near']<=255 and c['near']-c['far']>=10;self.optical_cal=c
  except (OSError,ValueError,KeyError,TypeError,AssertionError):pass
  self.setStyleSheet('QComboBox{color:#e6eefb;background:#21344f;padding:8px;} QComboBox QAbstractItemView{color:#e6eefb;background:#21344f;selection-background-color:#365b7e;} QProgressBar{color:#e6eefb;border:1px solid #40566e;background:#17263b;text-align:center;min-height:22px;} QProgressBar::chunk{background:#326d91;}')
  box=QVBoxLayout(self);box.addWidget(note('六轴估计重力与运动加速度；九轴/地磁姿态需要有效三轴磁场校准。数值为低速轮询工程估算。'))
  self.mode=QComboBox();self.mode.addItems(['六轴：重力姿态（Yaw为相对角）','九轴融合：磁北姿态（需三轴校准）','地磁姿态：加速度＋磁场（需三轴校准）']);box.addWidget(self.mode)
  grid=QGridLayout();self.cube=Canvas('gyro');self.vector=VectorView();grid.addWidget(self.cube,0,0);grid.addWidget(self.vector,0,1);box.addLayout(grid)
  self.status=QLabel('正在读取…');self.status.setWordWrap(True);self.status.setStyleSheet('color:#67d8ef;font-size:15px');box.addWidget(self.status)
  self.values=QLabel('');self.values.setWordWrap(True);self.values.setStyleSheet('color:#d9e8f5;font-size:13px');box.addWidget(self.values)
  controls=QHBoxLayout();zero=QPushButton('静置校零');zero.clicked.connect(self.pose.calibrate);controls.addWidget(zero);reset=QPushButton('重置姿态参考');reset.clicked.connect(self.fusion.reset);controls.addWidget(reset)
  import subprocess
  cal=QPushButton('打开三轴指南针校准');cal.clicked.connect(lambda:subprocess.Popen(['/usr/local/bin/f8-compass','--three-axis']));controls.addWidget(cal);box.addLayout(controls)
  self.optical=QLabel('环境光/接近：等待驱动');self.optical.setWordWrap(True);self.optical.setStyleSheet('color:#d9e8f5;font-size:14px');box.addWidget(self.optical)
  self.light_bar=QProgressBar();self.light_bar.setRange(0,1000);self.light_bar.setFormat('低光对数显示（仅显示增强）');box.addWidget(self.light_bar)
  self.prox_bar=QProgressBar();self.prox_bar.setRange(0,255);self.prox_bar.setFormat('接近原始计数 %v / 255');box.addWidget(self.prox_bar)
  row=QHBoxLayout();far=QPushButton('记录无遮挡值（远）');far.clicked.connect(lambda:self.record_optical('far'));near=QPushButton('记录遮挡值（近）');near.clicked.connect(lambda:self.record_optical('near'));row.addWidget(far);row.addWidget(near);box.addLayout(row)
  box.addWidget(note('光照尚未做透光率/lux标定；接近ADC不是厘米，饱和时不判定远近。三轴磁校准不等于软铁补偿/导航精度。'))
 def update_sample(self,data):
  matrix=data.get('example_matrix',((1,0,0),(0,1,0),(0,0,1)));scaled=data.get('scaled',{});a=scaled.get('accel');w=scaled.get('anglvel')
  a=mapped(matrix,a) if a else None;w=mapped(matrix,w) if w else None
  self.state=self.fusion.advance(a,w,data.get('monotonic',time.monotonic()),data.get('magnet'),self.pose.bias)
  opt=dict(data.get('optical',{}))
  if opt.get('available') and self.optical_cal:
   c=self.optical_cal;raw=opt['proximity_raw'];delta=c['near']-c['far']
   if raw>=c['far']+.65*delta:self.near=True
   elif raw<=c['far']+.35*delta:self.near=False
   opt.update(near=self.near,calibrated=True,far_reference=c['far'],near_reference=c['near'])
  if opt.get('available'):
   dark=self.optical_cal.get('ambient_dark_raw',0) if self.optical_cal else 0
   opt.update(ambient_dark_raw=dark,ambient_dark_corrected_raw=max(0,opt['ambient_raw']-dark),display_scale='log1p; display enhancement only')
  self.state.update(optical=opt,monotonic=data.get('monotonic'),online=True,version=1)
  f=self.state
  if f.get('valid') and not self.initial_mode_set:
   self.initial_mode_set=True
   if f.get('absolute_valid'):self.mode.setCurrentIndex(1)
  mode=self.mode.currentIndex();key=['game_rotation_vector_wxyz','rotation_vector_wxyz','geomagnetic_rotation_vector_wxyz'][mode];q=f.get(key)
  self.cube.q=q or (1,0,0,0);self.cube.data={'valid':q is not None,'invalid_note':f.get('magnetic_status','等待有效磁场') if mode else f.get('status','等待读数')};self.cube.update();self.vector.data=f;self.vector.update()
  self.status.setText(self.pose.message+'\n'+f.get('magnetic_status',f.get('status','等待读数')))
  if f.get('valid'):
   angles=f.get('euler9_yaw_pitch_roll_deg') if mode==1 else f.get('euler6_yaw_pitch_roll_deg')
   if mode==2 and q:
    from sensor_fusion import euler
    angles=euler(q)
   self.values.setText(('所选姿态未就绪' if not angles else 'Yaw/Pitch/Roll  %+.1f° / %+.1f° / %+.1f°'%tuple(angles))+'\n'+('四元数 WXYZ  '+' '.join(f'{v:+.4f}' for v in q) if q else '绝对姿态暂不输出')+'\n线性加速度模长 %.3f m/s² · 重力修正%s'%(norm(f['linear_acceleration_m_s2']),'开启' if f['gravity_correction_active'] else '暂缓'))
   h=f.get('tilt_heading_deg') if mode==2 else f.get('heading_deg')
   self.values.setText(self.values.text()+('\n磁航向 %.1f°（已整体调转180°）'%h if mode>0 and h is not None else '\n六轴Yaw为相对角，不能代表磁北' if mode==0 else '\n竖屏顶部接近竖直，航向暂不输出'))
  opt=self.state.get('optical',{})
  if opt.get('available'):
   l=opt['ambient_raw'];p=opt['proximity_raw'];net=opt.get('ambient_dark_corrected_raw',l);self.light_bar.setValue(round(math.log1p(net)/math.log1p(4095)*1000));self.prox_bar.setValue(p);self.optical.setText(f'EM30918：环境光原值 {l} / 扣暗基线 {net}；接近ADC {p}'+((' · 近' if opt.get('near') else ' · 远') if opt.get('calibrated') and opt.get('near') is not None else ('（饱和，未标定）' if p==255 else '（未标定远近）')))
  else:self.optical.setText('环境光/接近：'+opt.get('error','未检测到已验证驱动'))
  if time.monotonic()-self.last_publish>.2:self.publish()
 def record_optical(self,which):
  opt=self.state.get('optical',{})
  if not opt.get('available'):QMessageBox.information(self,'等待数据','请先恢复环境光/接近传感器读数。');return
  raw=opt['proximity_raw']
  if which=='far':self.pending_far=raw;QMessageBox.information(self,'已记录无遮挡值',f'远值 {raw}。请用手靠近传感器，再点“记录遮挡值（近）”。');return
  if self.pending_far is None:QMessageBox.information(self,'先记录远值','先移开手，记录无遮挡值，再记录遮挡值。');return
  if raw-self.pending_far<10:QMessageBox.warning(self,'变化不足','近值需要比远值至少大10，请找准传感器位置并靠近后重试。原校准未覆盖。');return
  c={'version':1,'device':'EM30918/PID0x31','far':self.pending_far,'near':raw,'method':'user two-point ADC classification with 35/65 percent hysteresis; not distance in cm'}
  if self.optical_cal:
   for key in ['ambient_dark_raw','ambient_indoor_raw']:
    if key in self.optical_cal:c[key]=self.optical_cal[key]
  try:
   self.optical_path.parent.mkdir(parents=True,exist_ok=True)
   if self.optical_path.exists():
    from datetime import datetime
    self.optical_path.with_name('optical-calibration.backup-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.json').write_bytes(self.optical_path.read_bytes())
   self.optical_path.write_text(json.dumps(c,indent=2)+'\n')
  except OSError as e:QMessageBox.warning(self,'保存失败',str(e));return
  self.optical_cal=c;self.near=None;self.pending_far=None;QMessageBox.information(self,'接近校准已保存','已启用远/近显示。仅分类，不是厘米距离。')
 def publish(self):
  self.last_publish=time.monotonic()
  try:
   p=self.path.with_suffix('.tmp');p.write_text(json.dumps(self.state,ensure_ascii=False));p.chmod(0o600);p.replace(self.path)
  except OSError:pass
 def invalidate(self,reason):
  self.state={'online':False,'valid':False,'status':reason,'version':1,'monotonic':time.monotonic()};self.publish()
