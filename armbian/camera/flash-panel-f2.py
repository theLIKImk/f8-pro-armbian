#!/usr/bin/python3
"""F8 native Wayland light control, with a short-lived privileged pipe session."""
import sys
from pathlib import Path
from PyQt6.QtCore import QProcess,QTimer,Qt
from PyQt6.QtWidgets import QApplication,QGridLayout,QLabel,QMainWindow,QPushButton,QSlider,QSpinBox,QVBoxLayout,QWidget

class Window(QMainWindow):
 def __init__(self):
  super().__init__();self.setWindowTitle('F8 闪光灯');self.resize(540,400)
  box=QWidget();self.setCentralWidget(box);layout=QVBoxLayout(box)
  note=QLabel('亮度为 PWM 平均亮度。关闭窗口会熄灭闪光灯。');note.setWordWrap(True);layout.addWidget(note)
  self.status=QLabel();layout.addWidget(self.status)
  self.level_label=QLabel();layout.addWidget(self.level_label)
  self.level=QSlider(Qt.Orientation.Horizontal);self.level.setRange(1,100);self.level.setValue(25);self.level.setMinimumHeight(48);layout.addWidget(self.level)
  timing=QGridLayout();self.on=QSpinBox();self.off=QSpinBox()
  for value in [self.on,self.off]:value.setRange(100,5000);value.setSingleStep(100);value.setValue(500);value.setSuffix(' 毫秒');value.setMinimumHeight(44)
  timing.addWidget(QLabel('闪烁：亮的时间'),0,0);timing.addWidget(self.on,0,1)
  timing.addWidget(QLabel('闪烁：灭的时间'),1,0);timing.addWidget(self.off,1,1);layout.addLayout(timing)
  buttons=QGridLayout();self.buttons={}
  for index,(name,text) in enumerate([('pulse','短闪（0.5 秒）'),('steady','常亮'),('blink','循环闪烁'),('off','立即熄灭')]):
   b=QPushButton(text);b.setMinimumHeight(54);b.clicked.connect(lambda _,n=name:self.select(n));buttons.addWidget(b,index//2,index%2);self.buttons[name]=b
  layout.addLayout(buttons);self.message=QLabel('首次开启需要管理员验证。');self.message.setWordWrap(True);layout.addWidget(self.message)
  self.proc=QProcess(self);self.proc.readyReadStandardOutput.connect(self.output);self.proc.finished.connect(self.finished)
  self.proc.errorOccurred.connect(lambda _:self.message.setText('管理员验证程序未能启动。'))
  self.ready=False;self.pending=None;self.mode='off';self.closing=False;self.buffer=b''
  self.debounce=QTimer(self);self.debounce.setSingleShot(True);self.debounce.setInterval(120);self.debounce.timeout.connect(self.apply)
  self.level.valueChanged.connect(self.changed);self.on.valueChanged.connect(self.changed);self.off.valueChanged.connect(self.changed)
  self.timer=QTimer(self);self.timer.timeout.connect(self.update_state);self.timer.start(200)
  self.heartbeat=QTimer(self);self.heartbeat.timeout.connect(self.keepalive);self.heartbeat.start(1000)
  self.changed();self.update_state()
 def changed(self):
  self.level_label.setText(f'亮度：{self.level.value()}%')
  if self.mode in ['steady','blink']:self.debounce.start()
 def select(self,mode):
  self.debounce.stop();self.mode=mode;self.apply()
 def apply(self):
  command=self.mode
  if command in ['pulse','steady']:command+=f' {self.level.value()}'
  elif command=='blink':command+=f' {self.level.value()} {self.on.value()} {self.off.value()}'
  if self.ready:self.send(command)
  elif command=='off':self.pending='off' if self.proc.state()!=QProcess.ProcessState.NotRunning else None
  elif command!='off':
   self.pending=command
   if self.proc.state()==QProcess.ProcessState.NotRunning:
    self.message.setText('等待管理员验证…');self.buffer=b''
    self.proc.start('/usr/bin/pkexec',['/usr/libexec/f8-pro/flash-control.py','--session'])
 def send(self,value):
  if self.ready and self.proc.state()!=QProcess.ProcessState.NotRunning:self.proc.write((value+'\n').encode('ascii'))
 def output(self):
  self.buffer+=bytes(self.proc.readAllStandardOutput())
  while b'\n' in self.buffer:
   line,self.buffer=self.buffer.split(b'\n',1)
   if line==b'ready':
    self.ready=True
    if self.pending:self.send(self.pending);self.pending=None
   elif line==b'ok':self.message.setText('已应用；关闭窗口将自动熄灭。')
 def keepalive(self):
  if self.ready and self.mode in ['steady','blink']:self.send('keepalive')
 def update_state(self):
  try:
   state=dict(item.split('=',1) for item in Path('/sys/devices/platform/f8-flash/state').read_text().split())
   names={'off':'已熄灭','pulse':'短闪','steady':'常亮','blink':'循环闪烁'}
   self.status.setText(f"状态：{names.get(state['mode'],state['mode'])} · 当前输出 {state['output']}%")
   available=True
  except (OSError,ValueError,KeyError):self.status.setText('状态：F2 驱动未就绪');available=False
  for b in self.buttons.values():b.setEnabled(available)
 def finished(self,code,_):
  self.ready=False;self.pending=None;self.mode='off'
  if not self.closing:self.message.setText('控制已停止。' if code==0 else '验证取消、会话已占用或控制失败；请重试。')
  self.update_state()
 def closeEvent(self,event):
  self.closing=True;self.heartbeat.stop();self.debounce.stop()
  if self.ready:
   self.send('off');self.proc.closeWriteChannel();self.proc.waitForFinished(300)
  if self.proc.state()!=QProcess.ProcessState.NotRunning:self.proc.kill();self.proc.waitForFinished(300)
  event.accept()

if __name__=='__main__':
 app=QApplication(sys.argv);w=Window();w.show();sys.exit(app.exec())
