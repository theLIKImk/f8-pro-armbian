#!/usr/bin/python3
"""A real Wayland touch-event test; never synthesizes input or reads evdev."""
import json,math,sys,time
from pathlib import Path
from PyQt6.QtCore import QEvent,QPointF,QTimer,Qt
from PyQt6.QtGui import QColor,QEventPoint,QFont,QPainter,QPen
from PyQt6.QtWidgets import QApplication,QHBoxLayout,QPushButton,QVBoxLayout,QWidget

class Canvas(QWidget):
 def __init__(self):
  super().__init__();self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents,True)
  self.setMinimumSize(320,320);self.contacts={};self.trails={};self.peak=0;self.hold=None;self.hold_peak=0.;self.passed=False;self.frames=0;self.cancelled=0
  self.folder=Path.home()/'.cache/f8-multitouch-test';self.folder.mkdir(parents=True,exist_ok=True);self.folder.chmod(0o700)
  self.started=time.time();self.devices=[];self.dirty=True;self.last_save=0
  self.diagnostic_start=None;self.trace=None;self.instructions='点击下方“开始同步诊断”，再按此处提示操作。'
  self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(40)
 def event(self,e):
  if e.type() in [QEvent.Type.TouchBegin,QEvent.Type.TouchUpdate,QEvent.Type.TouchEnd,QEvent.Type.TouchCancel] and self.trace is not None:
   self.trace.write(json.dumps({'t':time.monotonic(),'event':e.type().name,'points':[{'id':p.id(),'state':p.state().name,'x':p.position().x(),'y':p.position().y()} for p in e.points()] if hasattr(e,'points') else []})+'\n')
  if e.type() in [QEvent.Type.TouchBegin,QEvent.Type.TouchUpdate,QEvent.Type.TouchEnd]:
   self.frames+=1;now={}
   for point in e.points():
    if point.state()!=QEventPoint.State.Released:
     now[point.id()]=point.position();trail=self.trails.setdefault(point.id(),[]);trail.append(point.position())
     if len(trail)>50:del trail[:-50]
   self.contacts=now;self.peak=max(self.peak,len(now))
   if len(now)>=5:
    if self.hold is None:self.hold=time.monotonic()
   else:
    if self.hold is not None:self.hold_peak=max(self.hold_peak,time.monotonic()-self.hold)
    self.hold=None
   dev=e.pointingDevice()
   if not self.devices:self.devices=[{'name':dev.name(),'maximum_points':dev.maximumPoints(),'type':str(dev.type())}]
   e.accept();self.dirty=True;self.update();return True
  if e.type()==QEvent.Type.TouchCancel:
   self.contacts={};self.hold=None;self.cancelled+=1;e.accept();self.dirty=True;self.update();return True
  return super().event(e)
 def tick(self):
  if self.diagnostic_start is not None:
   elapsed=time.monotonic()-self.diagnostic_start
   steps=[(5,'准备：请抬起所有手指'),(13,'单指：一根手指在蓝色区域缓慢画圈'),(16,'全部抬起，准备双指'),(25,'双指：两根手指按住并缓慢移动'),(28,'全部抬起，准备逐根五指'),(45,'逐根五指：每隔1秒放下一指，然后一起缓慢移动'),(48,'全部抬起，准备同时五指'),(60,'同时五指：五指一起按下并缓慢移动'),(65,'全部抬起，诊断即将完成')]
   step=next(((end,msg) for end,msg in steps if elapsed<end),None)
   self.instructions=f'{step[1]}（剩余 {max(1,int(step[0]-elapsed))} 秒）' if step else '采集已完成，请回复测试感受。'
   if step is None:
    self.diagnostic_start=None
    if self.trace is not None:self.trace.close();self.trace=None
  if self.hold is not None:
   self.hold_peak=max(self.hold_peak,time.monotonic()-self.hold)
   if self.hold_peak>=2 and not self.passed:self.passed=True;self.dirty=True
  if self.dirty and time.monotonic()-self.last_save>.5:self.save()
  self.update()
 def start_diagnostic(self):
  if self.diagnostic_start is not None:return
  flag=Path('/run/f8-touch-diagnostic/start')
  if not flag.exists() or flag.read_text().strip()!='0':
   self.instructions='采集服务尚未就绪或本轮已结束，请等待重新准备。';self.update();return
  self.reset();self.trace=(self.folder/'trace-r2.jsonl').open('w',buffering=1);(self.folder/'trace-r2.jsonl').chmod(0o600)
  self.diagnostic_start=time.monotonic();flag.write_text(str(self.diagnostic_start));self.tick()
 def save(self):
  data={'started':self.started,'updated':time.time(),'current_contacts':len(self.contacts),'maximum_simultaneous_contacts':self.peak,'five_contact_hold_seconds':round(self.hold_peak,2),'five_contact_count_passed':self.passed,'movement_acceptance':'requires_user_test','touch_frames':self.frames,'cancelled_sequences':self.cancelled,'devices':self.devices,'platform':QApplication.platformName(),'synthetic_input_used':False}
  p=self.folder/'results.json';temp=self.folder/'results.tmp';temp.write_text(json.dumps(data,indent=2)+'\n');temp.chmod(0o600);temp.replace(p);self.last_save=time.monotonic();self.dirty=False
 def paintEvent(self,e):
  p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.fillRect(self.rect(),QColor('#101a2d'))
  p.setPen(QColor('#ecf2ff'));p.setFont(QFont('Noto Sans',22,QFont.Weight.Bold));p.drawText(24,44,'F8 五点触摸测试')
  p.setFont(QFont('Noto Sans',13));p.drawText(24,77,self.instructions)
  p.setFont(QFont('Noto Sans',25,QFont.Weight.Bold));p.setPen(QColor('#68e6b4') if self.passed else QColor('#9dc7ff'))
  p.drawText(24,120,f'当前 {len(self.contacts)} 点  ·  已见最多 {self.peak} 点')
  p.setFont(QFont('Noto Sans',13));p.drawText(24,151,('五点数量已确认；跟踪流畅度仍需实测' if self.passed else f'五点保持：{min(2,self.hold_peak):.1f} / 2 秒') + f'  ·  系统取消 {self.cancelled} 次')
  p.setPen(QPen(QColor('#263853'),1))
  for x in range(40,self.width(),60):p.drawLine(x,180,x,self.height())
  for y in range(200,self.height(),60):p.drawLine(0,y,self.width(),y)
  for ident,pos in self.contacts.items():
   color=QColor.fromHsv((ident*67)%360,170,255);trail=self.trails.get(ident,[])
   p.setPen(QPen(color,3))
   for a,b in zip(trail,trail[1:]):p.drawLine(a,b)
   p.setBrush(QColor(color.red(),color.green(),color.blue(),65));p.setPen(QPen(color,3));p.drawEllipse(pos,37,37)
   p.setPen(QColor('white'));p.setFont(QFont('Noto Sans',17,QFont.Weight.Bold));p.drawText(pos+QPointF(-14,7),str(ident))
 def reset(self):
  self.contacts={};self.trails={};self.peak=0;self.hold=None;self.hold_peak=0.;self.passed=False;self.frames=0;self.cancelled=0;self.dirty=True;self.save();self.update()

class Window(QWidget):
 def __init__(self):
  super().__init__();self.setWindowTitle('F8 五点触摸测试');self.resize(900,760)
  layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);self.canvas=Canvas();layout.addWidget(self.canvas)
  row=QHBoxLayout();diag=QPushButton('开始同步诊断（65秒）');diag.clicked.connect(self.canvas.start_diagnostic);row.addWidget(diag)
  reset=QPushButton('重新测试');reset.clicked.connect(self.canvas.reset);row.addWidget(reset)
  fullscreen=QPushButton('切换全屏');fullscreen.clicked.connect(lambda:self.showNormal() if self.isFullScreen() else self.showFullScreen());row.addWidget(fullscreen)
  close=QPushButton('关闭');close.clicked.connect(self.close);row.addWidget(close);layout.addLayout(row)
 def closeEvent(self,e):
  self.canvas.save()
  if self.canvas.trace is not None:self.canvas.trace.close();self.canvas.trace=None
  super().closeEvent(e)
if __name__=='__main__':
 app=QApplication(sys.argv);app.setStyleSheet('QPushButton {min-height:44px;font-size:17px;}');window=Window();window.showFullScreen();sys.exit(app.exec())
