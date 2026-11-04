#!/usr/bin/python3
import argparse,json,os,time
from collections import deque
from pathlib import Path
from PyQt6.QtCore import QTimer,Qt,QEvent
from PyQt6.QtGui import QEventPoint,QPainter,QColor,QPen
from PyQt6.QtWidgets import QApplication,QLabel,QPushButton,QVBoxLayout,QWidget
p=argparse.ArgumentParser();p.add_argument('--round',required=True);a=p.parse_args()
app=QApplication([]);w=QWidget();w.setWindowTitle('F8 触摸上报率 · '+a.round);w.resize(780,680)
layout=QVBoxLayout(w);status=QLabel('等待采集器就绪…');status.setWordWrap(True);status.setStyleSheet('font-size:24px');layout.addWidget(status)
flag=Path('/run/user')/str(os.getuid())/('f8-touch-rate-'+a.round+'.start')
button=QPushButton('开始20秒测试');button.setMinimumHeight(56);layout.addWidget(button)
def begin():
 flag.write_text('start\n');button.setEnabled(False);button.setText('已开始，请在蓝色区域画圈')
button.clicked.connect(begin)
class Area(QLabel):
 def __init__(self):
  super().__init__('先点上方“开始20秒测试”\n再在蓝色区域用一根手指连续画圈\n请持续移动，观察绿色触点是否跟手。')
  self.points=[];self.trail=deque(maxlen=150)
  self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents,True);self.setAlignment(Qt.AlignmentFlag.AlignCenter);self.setMinimumHeight(480)
  self.setStyleSheet('background:#183c67;color:white;border-radius:14px;font-size:24px;')
 def event(self,e):
  if e.type() in [QEvent.Type.TouchBegin,QEvent.Type.TouchUpdate,QEvent.Type.TouchEnd,QEvent.Type.TouchCancel]:
   self.points=[] if e.type() in [QEvent.Type.TouchEnd,QEvent.Type.TouchCancel] else [p.position() for p in e.points() if p.state()!=QEventPoint.State.Released]
   if self.points:self.trail.append(self.points[0])
   else:self.trail.clear()
   self.update();e.accept();return True
  return super().event(e)
 def paintEvent(self,e):
  super().paintEvent(e);painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  painter.setPen(QPen(QColor(90,230,255,180),4))
  trail=list(self.trail)
  for a,b in zip(trail,trail[1:]):painter.drawLine(a,b)
  painter.setBrush(QColor(100,255,200,190))
  for point in self.points:painter.drawEllipse(point,20,20)
layout.addWidget(Area());path=Path('/run')/('f8-touch-rate-'+a.round+'.json')
def update():
 try:
  d=json.loads(path.read_text());phase=d['phase']
  if phase=='waiting_for_touch':text='准备好后先点“开始20秒测试”，再到蓝色区域画圈。'
  elif phase=='capturing':text=f"正在采集，请继续画圈：还剩 {max(0,20-int(time.monotonic()-d['start_monotonic']))} 秒"
  elif phase=='finished':
   rate=d['summary']['irq']['median_hz'];text='采集完成，可以抬手。'+(f'\n原始中断节奏约 {rate:.1f} Hz' if rate else '\n有效数据不足')
  else:text='采集状态：'+phase+' '+d.get('error','')
  status.setText(text)
 except (OSError,ValueError,KeyError):pass
timer=QTimer(w);timer.timeout.connect(update);timer.start(200);update();w.show();app.exec()
